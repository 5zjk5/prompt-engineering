# https://docs.langchain.com/oss/python/langchain/context-engineering#messages
# 发送给LLM的提示信息由消息组成。管理消息内容至关重要，以确保LLM获得正确的信息并做出正确的回应。

# 下面是关键代码，展示了如何覆盖请求中的消息、工具和模型、响应格式：
# request = request.override(messages=messages)  # 覆盖请求中的消息  
# request = request.override(tools=tools)  # 修改请求中的工具  
# request.tools = tools  # 或者这种写法
# request = request.override(model=model)  # 修改模型
# request = request.override(response_format=SimpleResponse)  # 修改响应格式，在 ./结构化输出中有示例代码

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from dataclasses import dataclass
from langgraph.store.memory import InMemoryStore


# 当与当前查询相关时，从 State 注入上传的文件上下文：
@wrap_model_call
def inject_file_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject context about files user has uploaded this session."""
    # Read from State: get uploaded files metadata
    uploaded_files = request.state.get("uploaded_files", [])  

    if uploaded_files:
        # Build context about available files
        file_descriptions = []
        for file in uploaded_files:
            file_descriptions.append(
                f"- {file['name']} ({file['type']}): {file['summary']}"
            )

        file_context = f"""Files you have access to in this conversation:
{chr(10).join(file_descriptions)}

Reference these files when answering questions."""

        # Inject file context before recent messages
        messages = [  
            *request.messages
            {"role": "user", "content": file_context},
        ]
        request = request.override(messages=messages)  # 覆盖请求中的消息  

        # request = request.override(tools=tools)  # 修改请求中的工具  
        # request.tools = tools  # 或者这种写法

        # request = request.override(model=model)  # 修改模型

    return handler(request)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[inject_file_context]
)



# 从上期记忆 store 注入用户的电子邮件写作风格来指导起草：
@dataclass
class Context:
    user_id: str

@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    # 从运行上下文获取用户 ID
    user_id = request.runtime.context.user_id  

    # Read from Store: get user's writing style examples
    store = request.runtime.store  
    writing_style = store.get(("writing_style",), user_id)  

    if writing_style:
        style = writing_style.value
        # Build style guide from stored examples
        style_context = f"""Your writing style:
- Tone: {style.get('tone', 'professional')}
- Typical greeting: "{style.get('greeting', 'Hi')}"
- Typical sign-off: "{style.get('sign_off', 'Best')}"
- Example email you've written:
{style.get('example_email', '')}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)  # 覆盖请求中的消息  
        
        # request = request.override(tools=tools)  # 修改请求中的工具  
        # request.tools = tools  # 或者这种写法

        # request = request.override(model=model)  # 修改模型

    return handler(request)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[inject_writing_style],
    context_schema=Context,
    store=InMemoryStore()
)


