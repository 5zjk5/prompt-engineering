# https://docs.langchain.com/oss/python/langchain/agents#static-model

from ChatOpenAIModel_LangChian import ChatOpenAIModel
from langchain.tools import tool
from langchain.agents import create_agent
from middleware import handle_tool_errors, dynamic_model_selection, user_role_prompt
from typing import TypedDict


# Gemini llm
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-flash"
extra_body={
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 0,
            "include_thoughts": True
          }
        }
      }
    }
model = ChatOpenAIModel(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        extra_body=extra_body,
)


@tool
def search(query: str) -> str:
    """Search for information."""
    raise Exception("Search tool is not available.")  # 验证工具调用错误返回自定义消息


@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"


@tool
def hello() -> str:
    """问候工具"""
    return '你好啊！！！'


class Context(TypedDict):
    user_role: str


agent = create_agent(
    model=model,
    tools=[search, get_weather, hello],
    middleware=[handle_tool_errors, dynamic_model_selection, user_role_prompt],
    context_schema=Context  # The system prompt will be set dynamically based on context
)

# 直接调用，返回所有结果
# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "先调用天气工具查询北京，再调用搜索工具搜索你好"}]}
# )
# print(result)

# 流式调用，可以看到中间结果
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "先调用天气工具查询北京，再调用搜索工具搜索你好，最后调用问候工具"}]}, 
    stream_mode="values", context={"user_role": "expert"}):
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")

