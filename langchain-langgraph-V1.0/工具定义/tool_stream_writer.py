# https://docs.langchain.com/oss/python/langchain/tools#stream-writer
# 使用 流式传输工具执行时的自定义更新runtime.stream_writer。这对于向用户提供有关工具正在执行的操作的实时反馈非常有用。
# 在工具内部使用runtime.stream_writer，则必须在 LangGraph 执行上下文中调用该工具

from langchain.tools import tool, ToolRuntime

@tool
def get_weather(city: str, runtime: ToolRuntime) -> str:
    """Get weather for a given city."""
    writer = runtime.stream_writer

    # Stream custom updates as the tool executes
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")

    return f"It's always sunny in {city}!"
    