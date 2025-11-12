# https://docs.langchain.com/oss/python/langchain/tools#toolruntime
# 用于ToolRuntime通过单个参数访问所有运行时信息。只需将其添加runtime: ToolRuntime到工具签名中，即可自动注入，且不会暴露给 LLM

# https://docs.langchain.com/oss/python/langchain/tools#context
# 通过访问不可变的配置和上下文数据，如用户 ID、会话详细信息或特定于应用程序的配置runtime.context

from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from ChatOpenAIModel_LangChian import ChatOpenAIModel


USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com"
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com"
    }
}

@dataclass
class UserContext:
    user_id: str

@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return f"Account holder: {user['name']}\nType: {user['account_type']}\nBalance: ${user['balance']}"
    return "User not found"

# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-pro"
extra_body={
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 512,
            "include_thoughts": True
          }
        }
      }
    }
model = ChatOpenAIModel(
        api_key=API_KEY,
        base_url=BASE_URL,
        extra_body=extra_body,
        model=MODEL,
)

agent = create_agent(
    model,
    tools=[get_account_info],
    context_schema=UserContext,
    system_prompt="You are a financial assistant."
)

# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "What's my current balance?"}]},
#     context=UserContext(user_id="user123")
# )
# print(result)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What's my current balance?"}]}, 
    stream_mode="values", context=UserContext(user_id="user123")):
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
