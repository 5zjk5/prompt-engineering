# Agent 实现与中间件

本目录包含了基于 LangChain 和 LangGraph 的 Agent 实现，包括自定义模型、中间件和完整的 Agent 创建示例。

## 文件说明

### ChatOpenAIModel_LangChian.py
自定义的 OpenAI 兼容聊天模型实现，继承自 LangChain 的 BaseChatModel。该模型支持：

- **多种模型接口**：支持 OpenAI、Azure OpenAI 以及其他兼容 OpenAI API 的模型（如智谱、Gemini 等）
- **同步/异步调用**：提供同步和异步的生成与流式响应方法
- **思考功能支持**：区分思考内容和正文内容，分别标记 content_type 为 "reasoning" 和 "content"
- **工具绑定**：支持工具调用和并行工具调用
- **响应元数据**：记录延迟、块索引、总块数等元数据

### create_agent.py
Agent 创建和运行的主入口文件，展示了如何：

- 使用自定义模型创建 Agent
- 定义工具函数（搜索、天气查询、问候等）
- 应用中间件处理工具错误、动态模型选择和用户角色提示
- 实现流式调用以查看中间结果

### middleware.py
中间件实现，包含三个核心功能：

1. **handle_tool_errors**：处理工具执行错误，返回自定义错误消息
2. **dynamic_model_selection**：基于对话复杂度动态选择模型
3. **user_role_prompt**：根据用户角色动态生成系统提示

## 使用方法

### 1. 基本使用

```python
from ChatOpenAIModel_LangChian import ChatOpenAIModel
from langchain.agents import create_agent
from middleware import handle_tool_errors, dynamic_model_selection, user_role_prompt

# 初始化模型
model = ChatOpenAIModel(
    api_key="your-api-key",
    base_url="https://api.example.com/v1",
    model="model-name"
)

# 创建 Agent
agent = create_agent(
    model=model,
    tools=[your_tools],
    middleware=[handle_tool_errors, dynamic_model_selection, user_role_prompt],
    context_schema=Context
)

# 调用 Agent
result = agent.invoke({"messages": [{"role": "user", "content": "Your question"}]})
```

### 2. 流式调用

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Your question"}]}, 
    stream_mode="values", 
    context={"user_role": "expert"}
):
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
```

### 3. 自定义中间件

```python
from langchain.agents.middleware import wrap_tool_call, wrap_model_call, dynamic_prompt

@wrap_tool_call
def custom_tool_error_handler(request, handler):
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Custom error message: {str(e)}",
            tool_call_id=request.tool_call["id"]
        )

@dynamic_prompt
def custom_system_prompt(request: ModelRequest) -> str:
    # 根据上下文动态生成系统提示
    user_context = request.runtime.context.get("user_context", "default")
    return f"You are a helpful assistant for {user_context}."
```

## 特性对比

| 特性 | 标准实现 | 本实现 |
|------|---------|--------|
| 模型兼容性 | 仅限特定模型 | 支持所有 OpenAI 兼容模型 |
| 思考功能 | 部分支持 | 完整支持，区分思考与正文 |
| 中间件支持 | 基础支持 | 完整的中间件生态系统 |
| 错误处理 | 默认处理 | 自定义错误处理 |
| 动态提示 | 静态提示 | 基于上下文的动态提示 |
| 流式响应 | 基础支持 | 增强流式响应，包含元数据 |
