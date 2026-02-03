---
name: langchain-langgraph-coding-assistant
description: 当用户需要编写LangChain或LangGraph相关代码时，提供基于示例代码的编码辅助，包括RAG、Agent、工作流、工具定义、中间件等多种功能模块的实现指导。

---

# LangChain & LangGraph 编程助手

## 描述
本技能提供LangChain和LangGraph框架的编程辅助功能。当用户需要编写相关代码时，智能体将根据用户需求，参考resources文件夹中的示例代码，协助用户完成编码工作。resources文件夹包含了丰富的示例代码，涵盖RAG、Agent、工作流、工具定义、中间件、大模型调用等多个功能模块。

## 使用场景
当用户明确要求使用LangChain或LangGraph框架时，触发此技能：
- 明确提到使用LangChain编写代码
- 明确提到使用LangGraph编写代码
- 明确要求使用LangChain的API（如文档加载器、向量存储、工具等）
- 明确要求使用LangGraph的API（如StateGraph、函数式API、图API等）
- 要求参考resources文件夹中的LangChain/LangGraph示例代码
- 提到使用LangChain的特定功能（如Agent、RAG、中间件等）并暗示使用该框架
- 提到使用LangGraph的特定功能（如工作流、子图、中断等）并暗示使用该框架

## 指令

### 1. 需求分析
- 仔细分析用户的具体需求，确定需要实现的功能模块
- 识别用户使用的技术栈（LangChain、LangGraph或两者结合）
- 确定需要参考的示例代码所在的resources子目录

### 2. 查找相关示例
根据用户需求，在resources文件夹中查找对应的示例代码：

**RAG相关需求**
- 文档加载：resources/RAG/document_loaders.py
- 文本分割：resources/RAG/splitters.py
- 向量存储：resources/RAG/vectorstores_retrievers.py

**Agent相关需求**
- Agent创建：resources/agent/create_agent.py
- 中间件实现：resources/agent/middleware.py
- 自定义模型：resources/agent/ChatOpenAIModel_LangChian.py

**工作流相关需求**
- 函数式API：resources/functional(workflow)_api/
- 图API：resources/graph-api/
- 工作流对比：resources/工作流_图_对比/
  - 链式提示：chain_prompt_graph.py / chain_prompt_workflow.py
  - 评估器-优化器：evaluator_optimizer_graph.py / evaluator_optimizer_workflow.py
  - 并行化：parallelization_graph.py / parallelization_workflow.py
  - 计划器-工作者：planner_worker_graph.py / planner_worker_workflow.py
  - ReAct智能体：react_agent_graph.py / react_agent_workflow.py
  - 路由工作流：routing_graph.py / routing_workflow.py

**工具定义相关需求**
- 基本工具定义：resources/工具定义/tool_define.py
- Command工具：resources/工具定义/tool_command.py
- 内存存储：resources/工具定义/tool_memery_store.py
- 运行时上下文：resources/工具定义/tool_runtime_context.py
- 流式写入：resources/工具定义/tool_stream_writer.py

**中间件相关需求**
- 基于类的中间件：resources/中间件/class_based_middleware.py
- 基于装饰器的中间件：resources/中间件/decorator_based_middleware.py
- 上下文编辑：resources/中间件/context_editing.py
- 人工审核：resources/中间件/human_in_the_loop.py
- LLM工具选择：resources/中间件/llm_tool_selector.py
- 模型调用限制：resources/中间件/model_call_limit.py
- 模型回退：resources/中间件/model_fallback.py
- PII检测：resources/中间件/pii_detection.py
- 规划：resources/中间件/planning.py
- 摘要：resources/中间件/summary.py
- 工具调用限制：resources/中间件/tool_call_limit.py
- 工具重试：resources/中间件/tool_retry.py

**大模型调用相关需求**
- OpenAI兼容模型：resources/大模型调用/ChatOpenAIModel_LangChian.py
- Azure OpenAI：resources/大模型调用/Azure.py
- Gemini：resources/大模型调用/Gemini.py
- OpenAI官方API：resources/大模型调用/OpanAI.py

**Embedding相关需求**
- 本地Embedding：resources/embedding模型调用/local_embedding.py
- 云端Embedding：resources/embedding模型调用/cloud_embedding.py
- OpenAI兼容Embedding：resources/embedding模型调用/opanai_embedding.py

**上下文工程相关需求**
- 消息管理：resources/上下文工程/messages.py
- 系统提示：resources/上下文工程/system_prompt.py

**子图相关需求**
- 状态共享：resources/子图/share_state.py
- 多级子图：resources/子图/father_son_grandson_noShareState.py
- 持久化：resources/子图/add_persistence.py

**LangGraph中断相关需求**
- 审批或拒绝：resources/langgraph中断/approve_or_reject.py
- 工具中的中断：resources/langgraph中断/interrupts_in_tools.py
- 审查和编辑状态：resources/langgraph中断/review_and_edit_state.py
- 验证人工输入：resources/langgraph中断/validating_human_input.py

**时间旅行相关需求**
- 时间旅行功能：resources/时间旅行/use_time_travel.py

**MCP相关需求**
- 调用本地工具：resources/MCP/调用本地工具/
- 调用远程MCP服务：resources/MCP/调用远程mcp服务/

**完整案例参考**
- 计算器Agent：resources/案例/Calculator_Agent/
- 深度研究：resources/案例/Deep_Research/
- RAG Agent：resources/案例/RAG_Agent/

### 3. 代码实现
- 阅读相关示例代码的readme.md文件（如果存在），理解功能和使用方法
- 参考示例代码的实现方式和代码结构
- 根据用户的具体需求，编写符合要求的代码
- 确保代码风格与示例代码保持一致
- 如需要使用自定义模型，参考ChatOpenAIModel_LangChian.py的实现

### 4. 必要导入（重要）
在编写代码时，必须确保包含所有必要的导入语句。以下是常用导入说明：

**通用基础导入**
- typing: TypedDict, List, Any, Dict, Optional
- typing_extensions: TypedDict（用于更复杂的类型定义）

**LangChain核心导入**
- langchain_core.messages: AIMessage, HumanMessage, SystemMessage, ToolMessage
- langchain_core.prompts: ChatPromptTemplate
- langchain_core.output_parsers: StrOutputParser
- langchain_core.runnables: RunnablePassthrough
- langchain.tools: tool
- langchain.agents: create_agent

**LangGraph图API导入**
- langgraph.graph: StateGraph, START, END, MessagesState
- langgraph.graph.message: add_messages
- langgraph.checkpoint.memory: InMemorySaver
- langgraph.types: interrupt

**LangGraph函数式API导入**
- langgraph.func: entrypoint, task

**LangChain Agent中间件导入**
- langchain.agents.middleware: before_model, after_model, wrap_model_call, wrap_tool_call, AgentState, ModelRequest, ModelResponse, dynamic_prompt
- langgraph.runtime: Runtime

**LangChain文档加载器导入**
- langchain_community.document_loaders.csv_loader: CSVLoader
- langchain_community.document_loaders: JSONLoader, BSHTMLLoader
- langchain_docling.loader: DoclingLoader

**LangChain文本分割器导入**
- langchain_text_splitters: RecursiveCharacterTextSplitter, CharacterTextSplitter, MarkdownHeaderTextSplitter, RecursiveJsonSplitter

**LangChain向量存储导入**
- langchain_chroma: Chroma
- langchain_core.vectorstores: VectorStore
- langchain_core.embeddings: Embeddings

**LangChain Embedding导入**
- langchain_openai: OpenAIEmbeddings
- langchain_community.embeddings: HuggingFaceEmbeddings

**LangChain模型导入**
- langchain_openai: ChatOpenAI
- langchain_azure_chat_models: AzureChatOpenAI
- langchain_google_genai: ChatGoogleGenerativeAI

**LangChain RAG导入**
- langchain.chains: RetrievalQA
- langchain_core.runnables: RunnablePassthrough

**自定义模型导入**
- ChatOpenAIModel_LangChian: ChatOpenAIModel（如果使用resources中的自定义模型）

**可视化导入**
- IPython.display: Image, display

**其他常用导入**
- asyncio, uuid, time, os, pathlib.Path

**导入注意事项**
1. 在提供代码时，必须包含所有使用的导入语句
2. 如果代码中使用了某个类或函数，必须在导入部分包含对应的导入
3. 对于自定义的类或函数，需要明确说明其来源或提供完整定义
4. 建议将导入语句按照功能分组，便于阅读和维护
5. 如果使用了第三方库，需要提醒用户安装相应的依赖包

### 5. 代码说明
- 提供清晰的代码注释，说明关键逻辑
- 解释代码的工作原理和使用方法
- 指出代码中使用的LangChain/LangGraph核心概念和API
- 如涉及复杂功能，提供使用示例

### 6. 注意事项
- 不要修改resources文件夹中的任何示例代码
- 参考示例代码时，理解其设计思路和实现方式
- 根据用户实际需求进行适配和调整
- 确保代码的正确性和可运行性
- 如涉及API密钥等敏感信息，提醒用户自行配置

**常见错误及解决方案**

1. 缺少导入语句
   - 错误：NameError: name 'AIMessage' is not defined
   - 解决：确保导入了 from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

2. 缺少类型定义
   - 错误：NameError: name 'TypedDict' is not defined
   - 解决：确保导入了 from typing import TypedDict 或 from typing_extensions import TypedDict

3. 缺少工具装饰器
   - 错误：工具函数无法被识别
   - 解决：确保导入了 from langchain.tools import tool 并使用 @tool 装饰器

4. 缺少状态定义
   - 错误：NameError: name 'State' is not defined
   - 解决：确保定义了状态类，例如 class State(TypedDict): ...

5. 缺少图API导入
   - 错误：NameError: name 'StateGraph' is not defined
   - 解决：确保导入了 from langgraph.graph import StateGraph, START, END

6. 缺少中间件导入
   - 错误：NameError: name 'before_model' is not defined
   - 解决：确保导入了 from langchain.agents.middleware import before_model, after_model, ...

7. 自定义模型未导入
   - 错误：ModuleNotFoundError: No module named 'ChatOpenAIModel_LangChian'
   - 解决：确保自定义模型文件在正确路径，或提供完整的模型实现代码

8. 第三方库未安装
   - 错误：ModuleNotFoundError: No module named 'langchain_chroma'
   - 解决：提醒用户安装相应的依赖包，例如 pip install langchain-chroma

**代码质量保证**
- 在提供代码前，检查所有导入是否完整
- 确保所有使用的类和函数都有对应的导入
- 对于自定义的类或函数，提供完整的实现或明确说明来源
- 建议用户在运行代码前安装必要的依赖包
