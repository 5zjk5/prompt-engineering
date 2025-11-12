# https://docs.langchain.com/oss/python/langchain/middleware#model-fallback
# 当主模型失效时，自动回退到备用模型。
# 非常适合：
# 构建能够应对模型故障的弹性代理
# 通过退而求其次选择更便宜的型号来优化成本。
# OpenAI、Anthropic 等供应商之间的冗余。

from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware


agent = create_agent(
    model="openai:gpt-4o",  # Primary model
    tools=[],
    middleware=[
        ModelFallbackMiddleware(
            "openai:gpt-4o-mini",  # Try first on error 可以是模型字符串（例如，"openai:gpt-4o-mini"）或模型BaseChatModel实例。
            "anthropic:claude-3-5-sonnet-20241022",  # Then this
        ),
    ],
)
