# https://docs.langchain.com/oss/python/langchain/middleware#tool-call-limit
# 每一轮对话，限制
# 将工具调用次数限制为特定工具或所有工具。
# 适合：
# 防止过度调用昂贵的外部 API
# 限制网络搜索或数据库查询
# 对特定工具的使用频率实施限制

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware


# 不指定 tool_name 对所有工具生效
global_limiter = ToolCallLimitMiddleware(
    thread_limit=20,
    run_limit=10
)

# Limit specific tool
search_limiter = ToolCallLimitMiddleware(
    tool_name="search",  # 指定工具名
    thread_limit=5,  # 线程级限制，每个线程最多调用 5 次线程中所有运行的总工具调用次数上限。默认无限制。    
    run_limit=3,  # 单次调用中工具调用次数的上限。默认无限制。
    exit_behavior="end",  # 超出限制时的退出行为，"end" 或 "raise"。默认 "end"。
)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[global_limiter, search_limiter],
)
