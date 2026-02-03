# https://docs.langchain.com/oss/python/langchain/middleware#model-call-limit
# 限制模型调用的次数，以防止无限循环或过高的成本。

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware


agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[
        ModelCallLimitMiddleware(
            thread_limit=10,  # 每线程最多10次呼叫（跨运行）
            run_limit=5,  # 每个运行最多5次呼叫（单次调用）
            exit_behavior="end",  # 或 "error" 抛出异常
        ),
    ],
)
