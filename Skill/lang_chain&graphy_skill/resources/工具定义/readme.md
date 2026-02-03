# 工具定义

本目录包含了基于LangChain和LangGraph框架的各种工具定义和实现，主要用于构建智能代理系统。

## 文件说明

### ChatOpenAIModel_LangChian.py
自定义的OpenAI兼容模型实现，支持同步和异步调用，包括流式响应。支持OpenAI和Azure OpenAI API，并提供了思考内容处理功能。

### tool_define.py
包含基本的工具定义示例：
- 数据库搜索工具
- 计算器工具
- 天气查询工具

### tool_command.py
实现了基于LangGraph的Command工具，用于更新代理状态和控制图执行流程：
- 清除对话历史
- 更新用户名

### tool_memery_store.py
实现了内存存储工具，用于在代理执行过程中保存和获取用户信息：
- 获取用户信息
- 保存用户信息

### tool_runtime_context.py
展示了如何使用ToolRuntime访问运行时信息和上下文数据：
- 获取账户信息
- 用户上下文管理

### tool_stream_writer.py
演示了如何使用流式写入器提供工具执行的实时反馈：
- 天气查询流式输出
