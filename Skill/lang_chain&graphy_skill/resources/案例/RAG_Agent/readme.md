# RAG (检索增强生成) 实现流程

本项目实现了一个完整的RAG（Retrieval-Augmented Generation）系统，通过检索相关文档来增强大模型的回答能力。

## RAG实现流程

### 1. 数据加载 (data_loader.py)
支持多种格式的文档加载：
- PDF：使用PyPDFLoader加载
- Word文档：使用DoclingLoader加载
- CSV：使用CSVLoader加载
- HTML：使用BSHTMLLoader加载
- JSON/JSONL：使用JSONLoader加载
- Markdown：使用DoclingLoader加载
- 其他文本文件：直接读取内容

### 2. 文档分割 (data_split.py)
根据不同文档类型采用不同的分割策略：
- Markdown：按标题层级分割，保留标题结构
- JSON：递归分割JSON结构，处理嵌套数据
- 代码：按语言特定规则分割（如Python）
- 其他文本：使用递归字符分割器，设置重叠部分防止上下文丢失

### 3. 向量化 (data_embedding.py)
使用阿里云的text-embedding-v4模型将文本转换为向量：
```python
embeddings = OpenAIEmbeddings(
    model="text-embedding-v4",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    tiktoken_enabled=False,  # 非OpenAI模型必需设置
    check_embedding_ctx_length=False  # 非OpenAI模型必需设置
)
```

### 4. 向量存储 (data_embedding_to_vector.py)
支持三种向量存储方式：
- **内存存储**：InMemoryVectorStore，适合快速测试和小规模数据
- **Chroma数据库**：持久化存储，支持元数据过滤和复杂查询
- **FAISS索引**：高效相似度搜索，适合大规模数据

### 5. 数据检索 (data_retrieval.py)
提供多种检索策略：
- **相似度检索**：基于向量相似度返回最相关的文档
- **带分数的相似度检索**：返回文档及其相似度分数
- **最大边际相关性(MMR)检索**：平衡相关性和多样性，避免结果过于相似

## 主流程 (data_process.py)

RAG系统的主要执行流程：

1. **加载数据**：从data目录加载所有支持的文档格式
2. **文档分割**：根据文档类型选择合适的分割策略
3. **向量化**：将分割后的文档转换为向量表示
4. **存储向量**：将向量存储到三种不同的向量数据库中
5. **检索查询**：根据用户查询检索相关文档片段

## 使用示例

```python
# 1. 加载数据
docs = load_data_by_type(data_files)

# 2. 分割文档
split_docs = spliter_docs(docs)

# 3. 初始化嵌入模型
embedding_model = DataEmbedding().init_embedding_model()

# 4. 创建向量存储
memory_store, chrome_store, faiss_store = EmbeddingVector().to_vector(split_docs, embedding_model)

# 5. 检索相关文档
data_retrieval = DataRetrieval(embedding_model, memory_store, chrome_store, faiss_store)
results = data_retrieval.retrieval("护发用什么好？")
```

## RAG工作原理

1. **索引阶段**：将文档分割成小块，转换为向量，存储在向量数据库中
2. **检索阶段**：将用户查询转换为向量，在向量数据库中找到最相似的文档片段
3. **生成阶段**：将检索到的文档片段作为上下文，提供给大模型生成回答

这种架构使大模型能够基于特定领域的知识回答问题，而不是仅依赖其训练数据。