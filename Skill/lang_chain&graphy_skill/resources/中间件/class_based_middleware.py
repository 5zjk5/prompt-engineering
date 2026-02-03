# https://docs.langchain.com/oss/python/langchain/middleware#class-based-middleware

# middleware=[middleware1, middleware2, middleware3]
# 在钩子按顺序运行之前：
#     middleware1.before_agent()
#     middleware2.before_agent()
#     middleware3.before_agent()
# 代理循环开始
#     middleware1.before_model()
#     middleware2.before_model()
#     middleware3.before_model()
# 像函数调用一样包装钩子嵌套：
#     middleware1.wrap_model_call()→ middleware2.wrap_model_call()→ middleware3.wrap_model_call()→ 模型
# 钩子按相反顺序运行后：
#     middleware3.after_model()
#     middleware2.after_model()
#     middleware1.after_model()
# 代理循环结束
#     middleware3.after_agent()
#     middleware2.after_agent()
#     middleware1.after_agent()


from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse, hook_config
from langgraph.runtime import Runtime
from typing import Callable
from typing import Any


# 节点式钩子
class LoggingMiddleware(AgentMiddleware):
    # 在执行流程中的特定点运行：
    #     before_agent- 代理启动之前（每次调用一次）
    #     before_model- 每次模型调用之前
    #     after_model- 每次模型响应后
    #     after_agent- 代理完成后（每次调用最多一次）
    # 意思就是把那这四个装饰器的方法用类包装都实现了，

    def __init__(self, max_messages: int = 50):
        super().__init__()
        self.max_messages = max_messages

    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None

    # 示例 直接跳到结束节点
    # @hook_config(can_jump_to=["end", "tools"])
    # def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    #     if len(state["messages"]) == self.max_messages:
    #         return {
    #             "messages": [AIMessage("Conversation limit reached.")],
    #             "jump_to": "end"
    #         }
    #     return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None
    
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call agent with {len(state['messages'])} messages")
        return None
    
    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Agent completed with {len(state['messages'])} messages")
        return None



# 节点式钩子自定义状态
class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

class CallCounterMiddleware(AgentMiddleware[CustomState]):
    state_schema = CustomState

    @hook_config(can_jump_to=["end", "tools"])
    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        # Access custom state properties
        count = state.get("model_call_count", 0)

        if count > 10:
            return {"jump_to": "end"}

        return None

    def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        # Update custom state
        return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="openai:gpt-4o",
    middleware=[CallCounterMiddleware()],
    tools=[...],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})



# 缠绕式挂钩
class RetryMiddleware(AgentMiddleware):
    # 在调用处理程序时拦截执行和控制：
    # wrap_model_call- 围绕每个模型调用
    # wrap_tool_call- 围绕每个工具调用
    # 您可以决定是否调用处理程序零次（短路）、一次（正常流程）或多次（重试逻辑）。

    def __init__(self, max_retries: int = 3):
        super().__init__()
        self.max_retries = max_retries

    # 示例：模型重试中间件
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        for attempt in range(self.max_retries):
            try:
                return handler(request)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Retry {attempt + 1}/{self.max_retries} after error: {e}")

    # 示例：动态模型选择
    # def wrap_model_call(
    #     self,
    #     request: ModelRequest,
    #     handler: Callable[[ModelRequest], ModelResponse],
    # ) -> ModelResponse:
    #     # Use different model based on conversation length
    #     if len(request.messages) > 10:
    #         request.model = init_chat_model("openai:gpt-4o")
    #     else:
    #         request.model = init_chat_model("openai:gpt-4o-mini")
    #     return handler(request)

    # 示例：工具调用监控
    # def wrap_tool_call(
    #     self,
    #     request: ToolCallRequest,
    #     handler: Callable[[ToolCallRequest], ToolMessage | Command],
    # ) -> ToolMessage | Command:
    #     print(f"Executing tool: {request.tool_call['name']}")
    #     print(f"Arguments: {request.tool_call['args']}")

    #     try:
    #         result = handler(request)
    #         print(f"Tool completed successfully")
    #         return result
    #     except Exception as e:
    #         print(f"Tool failed: {e}")
    #         raise
