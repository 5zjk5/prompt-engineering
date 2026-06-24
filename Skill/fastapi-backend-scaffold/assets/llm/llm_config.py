"""大模型配置管理 — 在代码中集中配置多个模型服务。"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class LLMProviderConfig:
    """描述一个 OpenAI 兼容的大模型服务配置。"""
    name: str
    base_url: str
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    extra_body: Dict[str, Any] = field(default_factory=dict)


# 大模型服务配置列表。
# 如需配置多个模型，继续在列表中追加字典；重试时会按顺序自动切换。
# 请将下方示例替换为实际可用的模型服务配置。
LLM_PROVIDERS: List[Dict[str, Any]] = [
    {
        "name": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-your-api-key-here",
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 4096,
        "extra_body": {},
    },
    # 备用模型示例（重试时自动切换）
    # {
    #     "name": "qwen-plus",
    #     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    #     "api_key": "sk-your-api-key-here",
    #     "model": "qwen-plus",
    #     "temperature": 0.3,
    #     "max_tokens": 4096,
    #     "extra_body": {},
    # },
    # 支持 extra_body 传递额外参数的示例（如 top_k、chat_template_kwargs 等）
    # {
    #     "name": "qwen3.6-27b",
    #     "base_url": "https://your-api-endpoint/v1",
    #     "api_key": "sk-your-api-key-here",
    #     "model": "qwen3.6-27b-fp8",
    #     "temperature": 0.3,
    #     "max_tokens": 4096,
    #     "extra_body": {
    #         "top_k": 20,
    #         "chat_template_kwargs": {"enable_thinking": False},
    #     },
    # },
]


def _safe_int(value: str, default: int) -> int:
    """安全解析整数配置，解析失败时返回默认值。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: str, default: float) -> float:
    """安全解析浮点数配置，解析失败时返回默认值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_llm_retry_count() -> int:
    """读取大模型调用最大重试次数，默认重试 2 次。"""
    return max(0, _safe_int(os.getenv("LLM_RETRY_COUNT", "2"), 2))


def get_llm_non_stream_timeout() -> float:
    """读取非流式大模型调用整体超时时间，默认 60 秒。"""
    return max(1.0, _safe_float(os.getenv("LLM_NON_STREAM_TIMEOUT", "60"), 60.0))


def get_llm_stream_first_chunk_timeout() -> float:
    """读取流式大模型首个内容 chunk 超时时间，默认 10 秒。"""
    return max(1.0, _safe_float(os.getenv("LLM_STREAM_FIRST_CHUNK_TIMEOUT", "10"), 10.0))


def get_llm_providers() -> List[LLMProviderConfig]:
    """读取代码中配置的大模型服务列表。"""
    providers: List[LLMProviderConfig] = []
    for index, item in enumerate(LLM_PROVIDERS):
        providers.append(
            LLMProviderConfig(
                name=str(item.get("name") or f"provider_{index + 1}"),
                base_url=str(item["base_url"]),
                api_key=str(item["api_key"]),
                model=str(item["model"]),
                temperature=float(item["temperature"]),
                max_tokens=int(item["max_tokens"]),
                extra_body=dict(item.get("extra_body") or {}),
            )
        )
    return providers


def get_default_llm_provider() -> LLMProviderConfig:
    """读取默认大模型服务配置。"""
    providers = get_llm_providers()
    if not providers:
        raise RuntimeError("LLM_PROVIDERS 至少需要配置一个模型")
    return providers[0]
