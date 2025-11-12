# RAG (检索增强生成) 示例

本目录包含了各种 RAG (Retrieval-Augmented Generation) 相关的代码示例，展示了如何使用 LangChain 实现文档加载、文本分割和向量存储等核心功能。

## 文件列表

### 1. document_loaders.py
**功能**: 演示如何使用不同类型的文档加载器

该文件展示了如何使用 LangChain 的各种文档加载器来加载不同格式的文档，包括 CSV、JSON、JSONL、HTML 和 DOCX 等。

**主要加载器类型**:

1. **CSVLoader**
   - 用于加载 CSV 文件
   - 支持自定义分隔符、引用字符和字段名
   - 可指定源列，为每行创建文档时设置来源

2. **JSONLoader**
   - 用于加载 JSON 和 JSONL 文件
   - 支持 jq_schema 进行数据筛选
   - 可指定内容键来提取特定字段

3. **DoclingLoader**
   - 支持多种格式：PDF、DOCX、PPTX、HTML 等
   - 可解析文档布局、表格等复杂结构
   - 支持导出为文档块或 Markdown 格式

**使用场景**: 当需要从不同格式的文档中提取内容，并将其转换为 LangChain 可处理的文档格式时。

### 2. splitters.py
**功能**: 演示如何使用不同类型的文本分割器

该文件展示了如何使用 LangChain 的各种文本分割器，将长文档分割成更小的、适合处理的文本块。

**主要分割器类型**:

1. **RecursiveCharacterTextSplitter**
   - 基于文本结构的递归分割
   - 尝试保持较大的单元（如段落）完整
   - 如果单元超过块大小，移到下一级（如句子）
   - 推荐作为大多数使用场景的首选

2. **CharacterTextSplitter**
   - 基于长度的简单分割
   - 根据字符数或词元数量分割文本
   - 可自定义元数据

3. **MarkdownHeaderTextSplitter**
   - 专门用于 Markdown 文档的分割
   - 基于标题层级进行分割
   - 可配置是否保留标题

4. **RecursiveJsonSplitter**
   - 专门用于 JSON 数据的分割
   - 采用深度优先遍历，构建更小的 JSON 块
   - 可配置最小和最大块大小

5. **代码分割器**
   - 支持多种编程语言（Python、JavaScript 等）
   - 基于语言语法结构进行分割
   - 保持代码块的完整性

**使用场景**: 当需要将长文档分割成更小的、适合嵌入模型处理的文本块时。

### 3. vectorstores_retrievers.py
**功能**: 向量存储和检索器的示例代码

该文件目前是一个框架文件，包含了向量存储和检索器的相关文档链接和说明。
