# https://docs.langchain.com/oss/python/langchain/middleware#decorator-based-middleware
# 自定义中间件
# 对于只需要单个钩子的简单中间件，装饰器是添加功能的最快捷方式

# 在 agent/create_agent.py 有使用示例
# 在 ./短期记忆 中有使用示例

# 可用的装饰器
# Node 风格（在特定执行点运行）：
    # @before_agent- 代理启动之前（每次调用一次）
    # @before_model- 每次模型调用之前
    # @after_model- 每次模型响应后
    # @after_agent- 代理完成后（每次调用一次）
# 包装式（拦截和控制执行）：
    # @wrap_model_call- 围绕每个模型调用
    # @wrap_tool_call- 围绕每个工具调用
# 便利装饰公司：
    # @dynamic_prompt- 生成动态系统提示（相当于@wrap_model_call修改提示）

# 何时使用装饰器
# • 只需一个钩子
# • 无需复杂的配置

from langchain.agents.middleware import before_model, after_model, wrap_model_call, wrap_tool_call
from langchain.agents.middleware import AgentState, ModelRequest, ModelResponse, dynamic_prompt
from langchain.messages import AIMessage, ToolMessage
from langchain.agents import create_agent
from langgraph.runtime import Runtime
from typing import Any, Callable


# Node-style: logging before model calls
@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"About to call model with {len(state['messages'])} messages")
    return None


# Node-style: validation after model calls
@after_model(can_jump_to=["end"])
def validate_output(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1]
    if "BLOCKED" in last_message.content:
        return {
            "messages": [AIMessage("I cannot respond to that request.")],
            "jump_to": "end"
        }
    return None


# Wrap-style: retry logic
@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")


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


# Wrap-style: dynamic prompts
@dynamic_prompt
def personalized_prompt(request: ModelRequest) -> str:
    user_id = request.runtime.context.get("user_id", "guest")
    return f"You are a helpful assistant for user {user_id}. Be concise and friendly."


# Use decorators in agent
agent = create_agent(
    model="openai:gpt-4o",
    middleware=[log_before_model, validate_output, retry_model, personalized_prompt],
    tools=[...],
)
