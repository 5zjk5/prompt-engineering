# 中间件示例

本目录包含了 LangChain 中间件的各种使用示例，展示了如何通过中间件增强代理的功能和行为。

## 自定义中间件

### class_based_middleware.py
基于类的中间件实现示例，展示了如何创建自定义中间件类来处理代理执行过程中的各种事件。包含 LoggingMiddleware 和 CallCounterMiddleware 两个示例，分别用于记录代理调用日志和统计调用次数。

### decorator_based_middleware.py
基于装饰器的中间件实现示例，展示了如何使用 @before_model、@after_model 等装饰器来创建中间件。包含重试逻辑、动态提示等功能示例。


## 内置中间件

### context_editing.py
上下文编辑中间件示例，展示了如何使用 ContextEditingMiddleware 来修改对话上下文。示例中使用 ClearToolUsesEdit 清除工具使用记录，实现对话历史的精确控制。

### human_in_the_loop.py
人工审核中间件示例，展示了如何使用 HumanInTheLoopMiddleware 实现人工干预和审核功能。配置了对 write_file_tool、execute_sql_tool 和 read_data_tool 的不同中断策略。

### llm_tool_selector.py
LLM 工具选择器中间件示例，展示了如何使用 LLMToolSelectorMiddleware 实现工具的智能选择。适用于多工具场景，可以减少令牌使用量。

### llm_tool_emulator.py
LLM 工具模拟器中间件示例，展示了如何使用 LLMToolEmulator 来模拟工具执行。主要用于测试和开发环境，无需实际调用外部工具。

### model_call_limit.py
模型调用限制中间件示例，展示了如何使用 ModelCallLimitMiddleware 限制模型调用次数。防止无限循环和控制成本。

### model_fallback.py
模型回退中间件示例，展示了如何使用 ModelFallbackMiddleware 在主模型失效时自动回退到备用模型。适合构建能够应对模型故障的弹性代理。

### pii_detection.py
个人身份信息检测中间件示例，展示了如何使用 PIIMiddleware 检测和处理对话中的敏感信息。支持多种处理策略，如遮盖、哈希或阻止。

### planning.py
规划中间件示例，展示了如何使用 TodoListMiddleware 为复杂的多步骤任务添加待办事项列表管理功能。自动为代理提供 write_todos 工具和系统提示。

### summary.py
摘要中间件示例，展示了如何使用 SummarizationMiddleware 在接近会话次数上限时自动汇总对话历史记录。适合处理超出上下文窗口的长时间对话。

### tool_call_limit.py
工具调用限制中间件示例，展示了如何使用 ToolCallLimitMiddleware 限制工具调用次数。可以针对特定工具或所有工具设置限制。

### tool_retry.py
工具重试中间件示例，展示了如何使用 ToolRetryMiddleware 使用可配置的指数退避算法自动重试失败的工具调用。提高网络依赖型工具的可靠性。


