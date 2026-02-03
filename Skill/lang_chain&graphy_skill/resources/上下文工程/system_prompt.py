# https://docs.langchain.com/oss/python/langchain/context-engineering#system-prompt
# 系统提示设定了 LLM 的行为和功能。不同的用户、情境或对话阶段需要不同的指令。成功的代理会利用记忆、偏好和配置，根据对话的当前状态提供正确的指令。

# agent/create_agent.py 中有使用示例

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from dataclasses import dataclass
from langgraph.store.memory import InMemoryStore


# # 从状态中获取消息计数或对话上下文：
@dynamic_prompt
def state_aware_prompt(request: ModelRequest) -> str:
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    base = "You are a helpful assistant."

    if message_count > 10:
        base += "\nThis is a long conversation - be extra concise."

    return base

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[state_aware_prompt]
)



# 从长期记忆中访问用户偏好：
# 从运行时上下文访问用户 ID 或配置：
@dataclass
class Context:
    user_id: str

@dynamic_prompt
def store_aware_prompt(request: ModelRequest) -> str:
    # # 从运行时上下文访问用户 ID 或配置：
    user_id = request.runtime.context.user_id

    # 从长期记忆中访问用户偏好：
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    base = "You are a helpful assistant."

    if user_prefs:
        style = user_prefs.value.get("communication_style", "balanced")
        base += f"\nUser prefers {style} responses."

    return base

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[store_aware_prompt],
    context_schema=Context,
    store=InMemoryStore()
)





