"""OpenAI 兼容 API 客户端 — 支持多模型配置、超时和失败重试。"""

import asyncio
import logging
import time
from typing import AsyncIterator, Callable, Dict, List, Optional, Tuple

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.llm.llm_config import (
    LLMProviderConfig,
    get_llm_non_stream_timeout,
    get_llm_providers,
    get_llm_retry_count,
    get_llm_stream_first_chunk_timeout,
)

logger = logging.getLogger(__name__)

_clients: Dict[Tuple[str, str], AsyncOpenAI] = {}


def _provider_key(provider: LLMProviderConfig) -> Tuple[str, str]:
    """生成模型服务客户端缓存 key，避免把 api_key 写入日志。"""
    return provider.name, provider.base_url


def get_llm_client(provider: LLMProviderConfig) -> AsyncOpenAI:
    """获取指定模型服务的 OpenAI 兼容客户端。"""
    key = _provider_key(provider)
    if key not in _clients:
        _clients[key] = AsyncOpenAI(
            base_url=provider.base_url,
            api_key=provider.api_key,
            timeout=get_llm_non_stream_timeout(),
        )
    return _clients[key]


def _is_retryable_error(exc: Exception) -> bool:
    """判断大模型调用异常是否适合重试。

    任何错误都切换模型重试（包括 400 BadRequestError 等），
    流式调用已吐内容时由调用方 first_content_yielded 保护，不在此处判断。
    """
    return True


def _order_providers(
    providers: List[LLMProviderConfig], preferred_model: Optional[str]
) -> List[LLMProviderConfig]:
    """按用户首选模型重排 provider 列表，首选模型排在最前，其余保持原序。"""
    if not preferred_model:
        return providers
    for i, p in enumerate(providers):
        if p.name == preferred_model or p.model == preferred_model:
            return [providers[i]] + providers[:i] + providers[i + 1 :]
    return providers


def _select_provider(providers: List[LLMProviderConfig], model: Optional[str], attempt: int) -> LLMProviderConfig:
    """按重试轮次选择模型配置，显式传入 model 时只覆盖模型名不影响服务选择。"""
    provider = providers[attempt % len(providers)]
    if model:
        return LLMProviderConfig(
            name=provider.name,
            base_url=provider.base_url,
            api_key=provider.api_key,
            model=model,
            temperature=provider.temperature,
            max_tokens=provider.max_tokens,
            extra_body=provider.extra_body,
        )
    return provider


async def chat_completion(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    logger: Optional[logging.Logger] = None,
    preferred_model: Optional[str] = None,
    on_provider: Optional[Callable[[str], None]] = None,
    **kwargs,
):
    """统一的聊天补全调用，支持失败重试和备用模型切换。

    preferred_model 指定用户首选模型名称，会将其对应的 provider 排到最前优先使用。
    on_provider 回调在每次选定 provider 时触发，调用方可据此通知前端当前使用的模型。
    """
    log = logger or globals()["logger"]
    providers = get_llm_providers()
    if not providers:
        raise RuntimeError("未配置可用的大模型服务")
    providers = _order_providers(providers, preferred_model)
    retry_count = get_llm_retry_count()
    max_attempts = max(1, retry_count)
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        provider = _select_provider(providers, model, attempt)
        if on_provider:
            on_provider(provider.name)
        client = get_llm_client(provider)
        resolved_temperature = temperature if temperature is not None else provider.temperature
        resolved_max_tokens = max_tokens or provider.max_tokens
        request_kwargs = dict(kwargs)
        if provider.extra_body:
            request_kwargs["extra_body"] = {
                **provider.extra_body,
                **dict(request_kwargs.get("extra_body") or {}),
            }
        # 估算输入 token 数
        input_tokens = sum(count_tokens(m.get("content", ""), provider.model) for m in (messages or []))
        log.info(
            "LLM 调用参数: provider=%s, base_url=%s, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d, input_tokens≈%d, attempt=%d/%d, non_stream_timeout=%s, extra_params=%s",
            provider.name,
            provider.base_url,
            provider.model,
            resolved_temperature,
            resolved_max_tokens,
            stream,
            len(messages or []),
            input_tokens,
            attempt + 1,
            max_attempts,
            get_llm_non_stream_timeout(),
            sorted(request_kwargs.keys()),
        )
        try:
            # 用 asyncio.wait_for 做硬超时，防止服务端持续返回数据导致 SDK read timeout 形同虚设
            start_time = time.time()
            result = await asyncio.wait_for(
                client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    temperature=resolved_temperature,
                    max_tokens=resolved_max_tokens,
                    stream=stream,
                    **request_kwargs,
                ),
                timeout=get_llm_non_stream_timeout(),
            )
            elapsed = time.time() - start_time
            log.info(
                "LLM 调用完成: provider=%s, model=%s, attempt=%d/%d, 耗时=%.2fs",
                provider.name, provider.model, attempt + 1, max_attempts, elapsed,
            )
            return result
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_error(exc)
            log.warning(
                "LLM 调用失败: provider=%s, model=%s, attempt=%d/%d, retryable=%s, error_type=%s, error=%s",
                provider.name,
                provider.model,
                attempt + 1,
                max_attempts,
                retryable,
                type(exc).__name__,
                exc,
            )
            if not retryable or attempt >= max_attempts - 1:
                break

    # TimeoutError 等异常的 str() 可能为空，包装成可读消息避免前端显示空白
    if last_error and not str(last_error):
        raise RuntimeError(
            f"LLM 调用失败: {type(last_error).__name__} (已重试 {max_attempts} 次)"
        ) from last_error
    raise last_error or RuntimeError("LLM 调用失败")


async def chat_completion_stream(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
    preferred_model: Optional[str] = None,
    on_provider: Optional[Callable[[str], None]] = None,
    **kwargs,
) -> AsyncIterator[str]:
    """流式聊天补全，首个内容 chunk 超时后自动重试并切换备用模型。

    preferred_model 指定用户首选模型名称，会将其对应的 provider 排到最前优先使用。
    on_provider 回调在每次选定 provider 时触发，调用方可据此通知前端当前使用的模型。
    """
    log = logger or globals()["logger"]
    providers = get_llm_providers()
    if not providers:
        raise RuntimeError("未配置可用的大模型服务")
    providers = _order_providers(providers, preferred_model)
    max_attempts = max(1, get_llm_retry_count())
    first_chunk_timeout = get_llm_stream_first_chunk_timeout()
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        provider = _select_provider(providers, model, attempt)
        if on_provider:
            on_provider(provider.name)
        client = get_llm_client(provider)
        resolved_temperature = temperature if temperature is not None else provider.temperature
        resolved_max_tokens = max_tokens or provider.max_tokens
        request_kwargs = dict(kwargs)
        if provider.extra_body:
            request_kwargs["extra_body"] = {
                **provider.extra_body,
                **dict(request_kwargs.get("extra_body") or {}),
            }

        first_content_yielded = False
        stream_start_time = time.time()
        # 估算输入 token 数
        input_tokens = sum(count_tokens(m.get("content", ""), provider.model) for m in (messages or []))
        log.info(
            "LLM 流式调用参数: provider=%s, base_url=%s, model=%s, temperature=%s, max_tokens=%s, messages=%d, input_tokens≈%d, attempt=%d/%d, first_chunk_timeout=%s, extra_params=%s",
            provider.name,
            provider.base_url,
            provider.model,
            resolved_temperature,
            resolved_max_tokens,
            len(messages or []),
            input_tokens,
            attempt + 1,
            max_attempts,
            first_chunk_timeout,
            sorted(request_kwargs.keys()),
        )
        try:
            async def _create_stream_and_read_first_content():
                """创建流式响应并读取第一个有内容的 chunk。"""
                response = await client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    temperature=resolved_temperature,
                    max_tokens=resolved_max_tokens,
                    stream=True,
                    **request_kwargs,
                )
                iterator = response.__aiter__()
                while True:
                    chunk = await iterator.__anext__()
                    content = chunk.choices[0].delta.content if chunk.choices else ""
                    if content:
                        return iterator, content

            iterator, first_content = await asyncio.wait_for(
                _create_stream_and_read_first_content(),
                timeout=first_chunk_timeout,
            )
            first_content_yielded = True
            log.info(
                "LLM 流式首 chunk 到达: provider=%s, model=%s, attempt=%d/%d, 耗时=%.2fs",
                provider.name, provider.model, attempt + 1, max_attempts, time.time() - stream_start_time,
            )
            yield first_content

            async for chunk in iterator:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            log.info(
                "LLM 流式调用完成: provider=%s, model=%s, attempt=%d/%d, 总耗时=%.2fs",
                provider.name, provider.model, attempt + 1, max_attempts, time.time() - stream_start_time,
            )
            return
        except StopAsyncIteration:
            return
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_error(exc)
            log.warning(
                "LLM 流式调用失败: provider=%s, model=%s, attempt=%d/%d, retryable=%s, error_type=%s, error=%s",
                provider.name,
                provider.model,
                attempt + 1,
                max_attempts,
                retryable,
                type(exc).__name__,
                exc,
            )
            if first_content_yielded or not retryable or attempt >= max_attempts - 1:
                break

    # TimeoutError 等异常的 str() 可能为空，包装成可读消息避免前端显示空白
    if last_error and not str(last_error):
        raise RuntimeError(
            f"LLM 流式调用失败: {type(last_error).__name__} (已重试 {max_attempts} 次)"
        ) from last_error
    raise last_error or RuntimeError("LLM 流式调用失败")


async def chat_completion_full(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
    preferred_model: Optional[str] = None,
    **kwargs,
) -> str:
    """非流式聊天补全，返回完整文本。"""
    log = logger or globals()["logger"]
    response = await chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
        logger=logger,
        preferred_model=preferred_model,
        **kwargs,
    )
    content = response.choices[0].message.content if response.choices else ""
    default_model = get_llm_providers()[0].model if get_llm_providers() else ""
    log.debug("chat_completion_full: 输入%d条消息, 输出长度=%d, 模型=%s",
              len(messages), len(content or ""), model or default_model)
    return content


def count_tokens(text: str, model: str = None) -> int:
    """粗略估算 token 数（使用 tiktoken）。"""
    try:
        import tiktoken
        default_model = get_llm_providers()[0].model if get_llm_providers() else "gpt-4o"
        enc = tiktoken.encoding_for_model(model or default_model)
        return len(enc.encode(text))
    except Exception:
        return int(len(text) / 3)
