# 项目案例介绍
此仓库为 langchain 框架的案例集合，主要涵盖 prompt 工程、大模型应用、RAG 检索增强、Agent 智能体等多个技术方向的实践案例。每个案例都经过实际测试验证，可作为学习和项目开发的参考。

## 核心技术栈
- **大模型**: 智谱 GLM 系列、通义千问 Qwen 系列、百度千帆等
- **框架**: LangChain、LlamaIndex、FastAPI、React Agent
- **向量数据库**: ChromaDB、Faiss
- **工具组件**: Playwright、VLLM、Transformers

## 项目详细介绍

### 1. Prompt 自动优化
**路径**: `prompt自动优化/`  
**技术**: 智谱 GLM-4-airx 模型  
**功能**: 自动化优化用户输入的 prompt，提升大模型回答质量和准确率。支持多场景 prompt 优化，包括问答、创作、分析等类型。通过多轮迭代优化，显著提高 prompt 的有效性。

### 2. GLM法律行业大模型挑战赛道
**路径**: `GLM法律行业大模型挑战赛道(agent)/`  
**技术**: LangChain Agent + 智谱 GLM 模型  
**功能**: 针对法律行业的智能问答系统，支持法条查询、案例分析、合同审查等法律专业场景。基于阿里天池比赛项目，展示 Agent 在专业领域的应用实践。

### 3. LangChain Agent 综合实验
**路径**: `langchain中的agent使用/`  
**技术**: LangChain 多种 Agent 类型  
**功能**: 系统实验 LangChain 支持的各种 Agent 类型，包括 ConversationalAgent、StructuredChatAgent、PlanAndExecute 等。每种 Agent 都配有详细的使用场景说明和代码注释，是学习 Agent 技术的完整教程。

### 4. 专业智能识别系统
**路径**: `专业识别/`  
**技术**: LangChain RAG + 通义千问 Qwen 系列  
**功能**: 从大量专业中智能识别用户问题的相关专业领域。通过向量检索召回相关专业，再由大模型进行最终判断。支持教育咨询、职业规划等专业识别场景。

### 5. 句子语义相似度识别
**路径**: `句子语义相似识别/`  
**技术**: LangChain 批量调用 + Qwen 模型  
**功能**: 高精度识别两个句子的语义相似程度，支持中文语义理解。采用批量处理技术提高效率，适用于问答匹配、内容推荐、重复内容检测等场景。

### 6. 实体命名识别系统
**路径**: `实体识别/`  
**技术**: LangChain + 大模型 NER  
**功能**: 从文本中自动识别和提取命名实体，包括人名、地名、机构名、时间等。支持自定义实体类型，可应用于信息抽取、知识图谱构建等领域。

### 7. 智能问答系统 (Agent+RAG)
**路径**: `智能问答系统(Agent+RAG)/`  
**技术**: Agent + RAG + GLM-4 + LangChain  
**功能**: 基于 Agent 和 RAG 技术的问答系统，支持复杂问题的多步推理。能够自动规划查询步骤，结合知识库检索生成准确答案。适用于企业知识问答、技术支持等场景。

### 8. 自定义 Agent 实现
**路径**: `智能问答系统(Agent+RAG)-1/`  
**技术**: 自研 Agent 框架 + Plan-and-Execute  
**功能**: 完全自主实现的 Agent 框架，支持计划制定、步骤执行、结果汇总等完整流程。相比 LangChain 内置 Agent 更加灵活，但 token 消耗较高。展示了 Agent 的核心实现原理。

### 9. 电影评论智能检索
**路径**: `电影评论检索/`  
**技术**: GLM-4 + Prompt 工程  
**功能**: 通过精心设计的 prompt 模板，让模型能够从电影评论数据中准确检索相关信息。支持按情感、主题、演员等多维度检索，展示了 prompt 在数据检索中的应用技巧。

### 10. 评论情感分析识别
**路径**: `评论情感识别/`  
**技术**: Qwen 系列 + 情感词典  
**功能**: 结合大模型和中文情感词典的评论情感识别系统。支持正面、负面、中性情感判断，以及情感强度分析。可应用于产品评价分析、舆情监控等场景。

### 11. PDF 长文档理解
**路径**: `PDF文件理解/`  
**技术**: GLM-4-long + LangChain 文档处理  
**功能**: 测试大模型对长 PDF 文档的理解能力，支持 11 万字级别的长文本处理。集成了文档解析、分段、向量化等完整流程，31 秒内完成文档解析和问答，展示了长上下文模型的强大能力。

### 12. 《斗破苍穹》RAG 智能搜索
**路径**: `《斗破苍穹》RAG智搜/`  
**技术**: RAG + 智谱 GLM 系列 + LangGraph  
**功能**: 以热门小说《斗破苍穹》为测试对象，对比不同模型、分块策略、检索方法在小说问答场景下的效果。通过多组实验总结普通 RAG 的局限性和优化方向，是 RAG 技术研究的典型案例。

### 13. 数据分析智能体
**路径**: `data_analysic_agent/`  
**技术**: Agent + 数据分析 + 可视化  
**功能**: 智能数据分析助手，支持数据探索、自动分析建议生成、可视化报告输出等功能。用户只需提供数据和分析目标，Agent 就能自动完成数据分析流程并生成专业的分析报告。

### 14. 深度搜索引擎
**路径**: `deep_search-dev/`  
**技术**: FastAPI + Playwright + GLM-4.5-flash  
**功能**: 基于大模型的深度搜索引擎，支持多轮迭代搜索、智能内容爬取、深度分析总结。能够对用户提出的复杂主题进行全方位信息收集和分析，生成专业的研究报告。适用于市场调研、竞品分析、学术研究等场景。

### 15. 工具检索系统
**路径**: `tool_retrieval/`  
**技术**: ChromaDB + 混合检索 + FastAPI  
**功能**: 专业的工具管理和检索平台，支持稠密检索、稀疏检索、关键词检索和混合检索四种模式。集成了工具描述优化、假设性问题生成等高级功能，是构建工具生态系统的核心组件。

### 16. VLLM 推理加速
**路径**: `vllm推理/`  
**技术**: VLLM + Transformers 对比  
**功能**: 对比测试 VLLM 推理框架与传统 Transformers 的性能差异。在句子相似度任务上，VLLM 相比传统方式提速 10 倍以上，展示了新一代推理引擎的巨大优势。

### 17. 自定义 React Agent
**路径**: `自定义 React Agant/`  
**技术**: React Agent 框架  
**功能**: 实现论文《React: Synergizing Reasoning and Acting in Language Models》中的 Agent 架构，通过思考-行动-观察的循环模式解决复杂任务。配有详细的架构图和实现说明，是理解现代 Agent 设计的经典案例。

## 核心模块文件

### 模型加载与工具包
- **langchain_load_llm.py**: LangChain 大模型加载器，支持主流模型集成
  - 支持智谱 GLM、通义千问、百度千帆等主流大模型
  - 支持本地模型加载和在线 API 调用
  - 提供统一的模型调用接口

- **langchain_module.py**: LangChain 核心功能封装
  - 集成 Prompt、Chain、RAG、Tool、Agent 等核心组件
  - 提供标准化的工具函数和配置模板
  - 支持快速构建大模型应用

- **llamaindex_module.py**: LlamaIndex 功能封装
  - 支持文档索引、向量存储、检索增强
  - 提供多种索引策略和检索算法
  - 与 LangChain 无缝集成

### 环境配置

#### API 密钥配置 (key.env)
在项目根目录创建 `key.env` 文件，配置各大模型 API 密钥：
```
# 通义千问 (阿里云)
DASHSCOPE_API_KEY=your_dashscope_api_key

# 百度千帆
QIANFAN_AK=your_qianfan_access_key
QIANFAN_SK=your_qianfan_secret_key

# 智谱 AI
GLM_API_KEY=your_glm_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# ModelScope
MODELSCOPE_API_KEY=your_modelscope_api_key
```

#### 模型下载 (model/)
`model/` 目录用于存放本地模型文件，支持从 Hugging Face 下载的模型：
- Embedding 模型: text2vec、sentence-transformers 等
- 大语言模型: ChatGLM、Baichuan、Qwen 等
- 多模态模型: 视觉-语言模型等

## 学习资源

### 资料文档 (资料/)
`资料/` 目录包含丰富的学习材料：
- **AI 提示词设计指南.pdf**: 系统介绍 Prompt 工程方法论
- **AI 交互提示宝典.pdf**: 实用的 Prompt 技巧和最佳实践
- **20款 AI 工具精选.pdf**: 主流 AI 工具的功能对比和使用指南
- **提示题培训PPT-通用.pptx**: Prompt 工程技术培训课件

### 在线资源
- **LangChain Smith**: https://smith.langchain.com/hub
  - 类似 GitHub 的 Prompt 仓库平台
  - 提供大量优质的 Prompt 模板和案例
  - 支持 Prompt 版本管理和协作开发

## 快速开始

### 环境准备
1. 安装 Python 3.8+ 环境
2. 克隆项目仓库
3. 创建并配置 `key.env` 文件
4. 安装项目依赖（各项目目录下一般都有 requirements.txt）

### 运行示例
```bash
# 进入任意项目目录
cd "项目目录"

# 安装依赖
pip install -r requirements.txt

# 运行主程序
python main.py
```

### 学习路径建议
1. **基础入门**: 从 `langchain中的agent使用` 开始，了解 LangChain 核心概念
2. **Prompt 工程**: 学习 `prompt自动优化`，掌握 Prompt 设计技巧
3. **RAG 技术**: 通过 `《斗破苍穹》RAG智搜` 深入理解检索增强生成
4. **Agent 开发**: 研究 `智能问答系统(Agent+RAG)` 系列，掌握智能体开发
5. **性能优化**: 学习 `vllm推理`，了解大模型推理加速技术
6. **综合应用**: 探索 `deep_search-dev` 和 `tool_retrieval` 等高级应用

## 技术特色

### 1. 全面的大模型生态覆盖
- 涵盖国内外主流大模型：智谱 GLM、通义千问、百度千帆、OpenAI 等
- 支持多种模型调用方式：API 调用、本地部署、混合部署
- 提供模型性能对比和最佳实践建议

### 2. 深度的 LangChain 框架应用
- 全面覆盖 LangChain 核心组件：Prompt、Chain、RAG、Tool、Agent
- 提供多种 Agent 实现方案：ReAct、Plan-and-Execute、Self-Ask 等
- 结合实际业务场景，展示框架的最佳应用方式

### 3. 前沿的 RAG 技术实践
- 多种检索策略：稠密检索、稀疏检索、混合检索
- 多种分块策略：固定大小、语义分块、层次分块
- 多种重排序和优化技术：RRF、多向量、ColBERT 等

### 4. 完整的 Agent 开发体系
- 从简单 Agent 到复杂多 Agent 系统
- 从理论原理到工程实现的全链路覆盖
- 结合具体业务场景的实战案例

### 5. 工程化的最佳实践
- 完整的日志系统和错误处理机制
- 性能优化和监控方案
- 生产环境部署和运维经验

## 贡献与反馈

欢迎提交 Issue 和 Pull Request 来完善项目。如果您有新的案例想法或发现了问题，请随时联系我们。

### 联系方式
- 提交 Issue: 在 GitHub 仓库提交问题反馈
- 代码贡献: Fork 项目并提交 Pull Request
- 技术讨论: 通过项目的 Discussion 功能进行交流

## 许可证

本项目采用 MIT 许可证，详情请参见 LICENSE 文件。
