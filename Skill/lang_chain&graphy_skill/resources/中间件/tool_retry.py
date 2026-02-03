# https://docs.langchain.com/oss/python/langchain/middleware#tool-retry
# 使用可配置的指数退避算法自动重试失败的工具调用。
# 非常适合：
# 处理外部 API 调用中的瞬态故障
# 提高网络依赖型工具的可靠性
# 构建能够优雅地处理临时错误的弹性代理

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware


agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, database_tool],
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,  # 默认值："2" 首次调用后的最大重试次数（默认共 3 次）
            backoff_factor=2.0,  # default:"2.0"  指数退避的乘数。每次重试等待initial_delay * (backoff_factor ** retry_number)秒数。设置为 0.0 表示恒定延迟
            initial_delay=1.0,  # default:"1.0"  首次重试前的初始延迟时间（秒）
            max_delay=60.0,  # default:"60.0" 重试之间的最大延迟时间（以秒为单位）（限制指数级退避增长）
            jitter=True,  # default:"true" 是否在延迟中加入随机抖动（±25%）以避免群体雷鸣效应
            tools=[],  # 可选的工具列表或工具名称，用于指定要应用重试逻辑的工具。如果指定None，则应用于所有工具。
            retry_on=(Exception,),  # default:"(Exception,)" 可以是要重试的异常类型元组，也可以是接受异常并返回True是否应该重试的可调用对象。

            # 当所有重试次数都用尽时的行为。选项：
            # "return_message"- 返回包含错误详情的工具消息（允许 LLM 处理故障）
            # "raise"- 重新引发异常（停止代理执行）
            # 自定义可调用对象 - 该函数接收异常并返回 ToolMessage 内容的字符串。
            on_failure="return_message"  # edfault:"return_message"  
        ),
    ],
)
