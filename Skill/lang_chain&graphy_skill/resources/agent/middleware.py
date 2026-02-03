from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, ModelRequest, dynamic_prompt


@wrap_tool_call
def handle_tool_errors(request, handler):
    # https://docs.langchain.com/oss/python/langchain/agents#tool-error-handling
    # 自定义如何处理工具错误，请使用@wrap_tool_call装饰器创建中间件
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )


@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    # https://docs.langchain.com/oss/python/langchain/agents#dynamic-model
    # 动态选择模型，每次请求模型之前会调用这个方法，请使用@wrap_model_call修改请求中的模型的装饰器创建中间件
    """Choose model based on conversation complexity."""
    message = request.state["messages"][-1]
    if '问候' in message.content:
        print('检测到问候，使用高级模型')
    else:
        print('未检测到问候，使用基础模型')

    # request.model = model
    return handler(request)


@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    # https://docs.langchain.com/oss/python/langchain/agents#dynamic-system-prompt
    # context_schema=Context The system prompt will be set dynamically based on context 创建 agent 时需要传入 context_schema 参数
    """Generate system prompt based on user role."""
    user_role = request.runtime.context.get("user_role", "user")
    base_prompt = "You are a helpful assistant."

    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."

    return base_prompt
