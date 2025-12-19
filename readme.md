# 📚 仓库介绍
此仓库为大模型应用开发案例仓库，主要涵盖 prompt 工程、大模型应用、RAG 检索增强、Agent 智能体等多个技术方向的实践案例。文件夹名按照应用分类进行命名，可作为学习和项目开发的参考。

早期有些是使用了 LangChain 框架，主要是 v0.1 版本，主要模块代码再 langchain-v0.1 目录下。在 2025.10.20 开始，LangChain 框架更新到 v1.0 版本，是官方一个全新比较的稳定的版本，主要模块代码在 langchain-langgraph-V1.0 目录下。包含 agent，rag，中间件，模型调用，上下文工程，结构化输出，工作流，图等。


# 🌟 推荐项目
* 深度搜索(DeepResearch)  
  **路径**: `Agent/deep_search-dev/`  
  **技术**: FastAPI + Playwright + GLM-4.5-flash + 搜索工具  
  **功能**: 基于大模型的深度搜索引擎，支持多轮迭代搜索、智能内容爬取、深度分析总结。能够对用户提出的复杂主题进行全方位信息收集和分析，生成专业的研究报告。适用于市场调研、竞品分析、学术研究等场景。
* Prompt 自动优化  
  **路径**: `Prompt/prompt自动优化/`  
  **技术**: 智谱 GLM-4-airx 模型  
  **功能**: 自动化优化用户输入的 prompt，提升大模型回答质量和准确率。主要针对有正确标签的提示词优化，通过多轮迭代优化，显著提高 prompt 的有效性。
* 工具检索  
  **路径**: `Rag/tool_retrieval/`  
  **技术**: RAG（稠密，稀疏，关键词，混合） + Fastapi + Chroma 数据库 + 假设性问题  
  **功能**: 一套完整服务，包含服务接口，数据库，检索方法，工具假设性问题生成。用户输入问题后，通过检索假设性问题库，检索工具库，合并排序去重，得到最相关的工具，最终召回率 94%。
* 深度研究(DeepResearch-langgraph)  
  **路径**: `langchain-langgraph-V1.0/案例/Deep_Research/`  
  **技术**: langgraph-V1.0  
  **功能**: 官方开源，详细介绍看官方介绍就可以，这里拿过来作为学习 langgraph，改了些东西进行了适配 langgraph-v1.0，langchang-v1.0 版本，加了自定义日志，适配了某些参数更新问题，把所有子图都模块化，注释都改成中文了，使用自定义 langchian 兼容 openai 的模型，可以 debug 调试，不依赖 langsmith 可视化。
* Chat Agent Langgraph 
  **路径**: `Agent/chat_agent_langgraph/`  
  **技术**: 前端对话界面 + 后端fastapi + sqlite + langgraph-v1.0   
  **功能**: 纯用 AI 编写，后端 python 人工把控，使用 langgraph 搭建图片理解多轮对话 agent，搭配前端界面包含用户管理，会话管理等功能，多轮对话历史保存，langgraph 中长期记忆的使用，长期记忆的检索。  


# 🤖 Agent
* Chat Agent Langgraph 
  **路径**: `Agent/chat_agent_langgraph/`  
  **技术**: 前端对话界面 + 后端fastapi + sqlite + langgraph-v1.0   
  **功能**: 纯用 AI 编写，后端 python 人工把控，使用 langgraph 搭建图片理解多轮对话 agent，搭配前端界面包含用户管理，会话管理等功能，多轮对话历史保存，langgraph 中长期记忆的使用，长期记忆的检索。 
---
* React Agent  
  **路径**: `Agent/自定义 React Agant/`  
  **技术**: React Agent 框架  
  **功能**: Agent 的一种架构，实现论文《React: Synergizing Reasoning and Acting in Language Models》中的 Agent 架构，通过思考-行动-观察的循环模式解决复杂任务。配有详细的架构图和实现说明，是理解现代 React Agent 设计的经典案例。
---
* Task Plan Function Call Agent  
  **路径**: `Agent/task_plane_function_call_agent/`  
  **技术**: 任务拆解，任务执行，TPFC 架构 Agent 实现  
  **功能**: Agent 的一种架构，实现任务拆解、任务执行、函数调用等功能，基于 TPFC 架构。适用于需要复杂任务处理的场景，如项目管理、自动任务执行等。
---
* data_analysic_agent  
  **路径**: `Agent/data_analysic_agent/`  
  **技术**: 数据分析智能体  
  **功能**: 基于大模型的数据分析智能体，针对统计分析，如聚合操作、分组统计等，提供可视化分析结果输出报告。
---
* 深度搜索(DeepResearch)  
  **路径**: `Agent/deep_search-dev/`  
  **技术**: FastAPI + Playwright + GLM-4.5-flash + 搜索工具
  **功能**: 基于大模型的深度搜索引擎，支持多轮迭代搜索、智能内容爬取、深度分析总结。能够对用户提出的复杂主题进行全方位信息收集和分析，生成专业的研究报告。适用于市场调研、竞品分析、学术研究等场景。
---
* 深度搜索(DeepResearch-Go)  
  **路径**: `Agent/deep_search-dev-go/`  
  **技术**: FastAPI + Playwright + GLM-4.5-flash + 搜索工具(Googlesearch)  
  **功能**: 功能跟 Python 版本的深度搜索(DeepResearch) 相同，只是使用了 Go 语言实现。且是使用 AI 写的。
---
* GLM法律行业大模型挑战赛道  
  **路径**: `Agent/GLM法律行业大模型挑战赛道(agent)/`  
  **技术**: LangChain-v0.1 Agent + 智谱 GLM 模型  
  **功能**: 针对法律行业的智能问答系统，支持法条查询、案例分析、合同审查等法律专业场景。基于阿里天池比赛项目，展示 Agent 在专业领域的应用实践，主要用于学习。
---
* LangChain Agent 使用  
  **路径**: `Agent/gentlangchain中的agent使用/`  
  **技术**: LangChain 多种 Agent 类型  
  **功能**: 系统实验 LangChain-v0.1 支持的各种 Agent 类型，包括 ConversationalAgent、StructuredChatAgent、PlanAndExecute 等。每种 Agent 都配有详细的使用场景说明和代码注释，但找 v1.0 版本进行了大更新，用新版本的好一些。


# 📂 Rag
* 《斗破苍穹》RAG 智能搜索  
  **路径**: `Rag/《斗破苍穹》RAG智搜/`  
  **技术**: Langchain-v0.1 RAG + 智谱 GLM 系列 + LangGraph  
  **功能**: 以热门小说《斗破苍穹》为测试对象，对比不同模型、分块策略、检索方法在小说问答场景下的效果。通过多组实验总结普通 RAG 的局限性和优化方向。
---
* 电影评论智能检索 csv  
  **路径**: `Rag/电影评论检索/`  
  **技术**: GLM-4 + Prompt 工程  
  **功能**: 通过精心设计的 prompt 模板，让模型能够从电影评论数据中准确检索相关信息。支持按情感、主题、演员等多维度检索，基于 langchain-v0.1。
---
* 工具检索  
  **路径**: `Rag/tool_retrieval/`  
  **技术**: RAG（稠密，稀疏，关键词，混合） + Fastapi + Chroma 数据库 + 假设性问题  
  **功能**: 一套完整服务，包含服务接口，数据库，检索方法，工具假设性问题生成。用户输入问题后，通过检索假设性问题库，检索工具库，合并排序去重，得到最相关的工具，最终召回率 94%。


# 🤝 Rag + Agent
* 智能问答系统 (Agent+RAG)  
  **路径**: `Rag+Agent/智能问答系统(Agent+RAG)/`  
  **技术**: Agent + RAG + GLM-4 + LangChain-v0.1  
  **功能**: 基于 Agent 和 RAG 技术的问答系统，是阿里天池上的练习，text2sql 任务是 agent，招股书检索任务是 rag。直接使用的 langchain 的 agent 与 rag。
---
* 智能问答系统 (Agent+RAG)-1  
**路径**: `Rag+Agent/智能问答系统(Agent+RAG)-1/`  
**技术**: gent + RAG + GLM-4  
**功能**: 完全自主实现的 Agent 框架，Agent 架构为 Task Plan - Excute，先把任务规划出来，然后按照任务一步一步去执行，也就是先全部计划，然后执行的架构。


# 💡 Prompt
* Prompt 自动优化  
  **路径**: `Prompt/prompt自动优化/`  
  **技术**: 智谱 GLM-4-airx 模型  
  **功能**: 自动化优化用户输入的 prompt，提升大模型回答质量和准确率。主要针对有正确标签的提示词优化，通过多轮迭代优化，显著提高 prompt 的有效性。
---
* VLLM 推理加速  
  **路径**: `Prompt/vllm推理/`  
  **技术**: VLLM + Transformers 对比  
  **功能**: 对比测试 VLLM 推理框架与传统 Transformers 的性能差异。在句子相似度任务上，VLLM 相比传统方式提速 10 倍以上。
---
* 专业智能识别系统  
  **路径**: `Prompt/专业识别/`  
  **技术**: LangChain RAG + 通义千问 Qwen 系列  
  **功能**: 从大量专业中智能识别用户问题的相关专业领域。通过向量检索召回相关专业，再由大模型进行最终判断。
---
* 句子语义相似度识别  
  **路径**: `Prompt/句子语义相似识别/`  
  **技术**: LangChain 批量调用 + Qwen 模型  
  **功能**: 高精度识别两个句子的语义相似程度，支持中文语义理解。
---
* 实体命名识别系统  
  **路径**: `Prompt/实体识别/`  
  **技术**: LangChain + 大模型 NER  
  **功能**: 从文本中自动识别和提取命名实体，包括人名、地名、机构名、时间等。
---
* 评论情感分析识别  
  **路径**: `Prompt/评论情感识别/`  
  **技术**: Qwen 系列 + 情感词典  
  **功能**: 结合大模型和中文情感词典的评论情感识别系统。支持正面、负面、中性情感判断，以及情感强度分析。可应用于产品评价分析、舆情监控等场景。
---
* PDF 长文档理解  
  **路径**: `Prompt/PDF文件理解/`  
  **技术**: GLM-4-long + LangChain 文档处理   
  **功能**: 测试大模型对长 PDF 文档的理解能力，支持 11 万字级别的长文本处理。


# 🔧 langchain-v0.1
langchian 模块代码，这个版本当时这里这个模块主要集成了：  
1、RAG 流程（文档加载，分割，向量化入库，检索）  
2、提示词模版，链，工具，记忆，再 v1.0 这些不是重点，好想砍掉了。


# 🛠️ langchain-langgraph-V1.0
官方第一个大版本，基于 V1.0 的代码案例，保存下来当笔记了，这个版本对 agent 支持更多了，更好了。要运行一些示例，环境需匹配其中的 requirements.txt。


# ⚙️ llamaindex
llamaindex rag 使用，忘记哪个版本了。

