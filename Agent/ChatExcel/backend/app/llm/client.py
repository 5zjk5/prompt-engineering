"""OpenAI 兼容 API 客户端 — 支持多模型配置、超时和失败重试。"""

import asyncio
import logging
from typing import AsyncIterator, Dict, List, Optional, Tuple

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
    """判断大模型调用异常是否适合重试。"""
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError, asyncio.TimeoutError)):
        return True
    if isinstance(exc, APIError):
        status_code = getattr(exc, "status_code", None)
        return status_code is None or status_code >= 500
    return False


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
    **kwargs,
):
    """统一的聊天补全调用，支持失败重试和备用模型切换。"""
    providers = get_llm_providers()
    if not providers:
        raise RuntimeError("未配置可用的大模型服务")
    retry_count = get_llm_retry_count()
    max_attempts = max(1, retry_count + 1)
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        provider = _select_provider(providers, model, attempt)
        client = get_llm_client(provider)
        resolved_temperature = temperature if temperature is not None else provider.temperature
        resolved_max_tokens = max_tokens or provider.max_tokens
        request_kwargs = dict(kwargs)
        if provider.extra_body:
            request_kwargs["extra_body"] = {
                **provider.extra_body,
                **dict(request_kwargs.get("extra_body") or {}),
            }
        logger.info(
            "LLM 调用参数: provider=%s, base_url=%s, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d, attempt=%d/%d, non_stream_timeout=%s, extra_params=%s",
            provider.name,
            provider.base_url,
            provider.model,
            resolved_temperature,
            resolved_max_tokens,
            stream,
            len(messages or []),
            attempt + 1,
            max_attempts,
            get_llm_non_stream_timeout(),
            sorted(request_kwargs.keys()),
        )
        try:
            return await client.chat.completions.create(
                model=provider.model,
                messages=messages,
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
                stream=stream,
                **request_kwargs,
            )
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_error(exc)
            logger.warning(
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

    raise last_error or RuntimeError("LLM 调用失败")


async def chat_completion_stream(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> AsyncIterator[str]:
    """流式聊天补全，首个内容 chunk 超时后自动重试并切换备用模型。"""
    providers = get_llm_providers()
    if not providers:
        raise RuntimeError("未配置可用的大模型服务")
    max_attempts = max(1, get_llm_retry_count())
    first_chunk_timeout = get_llm_stream_first_chunk_timeout()
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        provider = _select_provider(providers, model, attempt)
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
        logger.info(
            "LLM 流式调用参数: provider=%s, base_url=%s, model=%s, temperature=%s, max_tokens=%s, messages=%d, attempt=%d/%d, first_chunk_timeout=%s, extra_params=%s",
            provider.name,
            provider.base_url,
            provider.model,
            resolved_temperature,
            resolved_max_tokens,
            len(messages or []),
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
            yield first_content

            async for chunk in iterator:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except StopAsyncIteration:
            return
        except Exception as exc:
            last_error = exc
            retryable = _is_retryable_error(exc)
            logger.warning(
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

    raise last_error or RuntimeError("LLM 流式调用失败")


async def chat_completion_full(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> str:
    """非流式聊天补全，返回完整文本。"""
    response = await chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
        **kwargs,
    )
    content = response.choices[0].message.content if response.choices else ""
    default_model = get_llm_providers()[0].model if get_llm_providers() else ""
    logger.debug("chat_completion_full: 输入%d条消息, 输出长度=%d, 模型=%s",
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
