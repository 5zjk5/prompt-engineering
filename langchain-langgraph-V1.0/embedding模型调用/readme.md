# Embedding 模型调用

本目录包含了本地和云端 Embedding 模型的调用实现，支持多种模型和调用方式。

## 文件说明

### local_embedding.py
本地 Embedding 模型加载和使用实现，基于 HuggingFace 和 sentence_transformers。

主要功能：
- **自动识别模型来源**：支持本地路径和 HuggingFace 仓库ID
- **设备选择**：支持 CPU 和 GPU 设备
- **简单易用**：提供统一的加载接口

### cloud_embedding.py
云端 Embedding 模型封装实现，以阿里云百炼为例，展示了如何将非标准 OpenAI 兼容的 Embedding 服务封装为 LangChain 兼容接口。

主要功能：
- **自定义封装**：继承 LangChain 的 Embeddings 基类
- **同步/异步支持**：提供同步和异步方法
- **错误处理**：完善的异常处理机制
- **批量处理**：支持单文本和多文本批量嵌入

### opanai_embedding.py
OpenAI 兼容接口的 Embedding 模型调用示例，展示了如何使用 langchain_openai 库调用各种兼容 OpenAI API 格式的 Embedding 服务。

主要功能：
- **多平台支持**：支持 ModelScope、阿里云等提供 OpenAI 兼容 API 的平台
- **参数配置**：提供完整的 API 参数配置示例
- **非标准模型支持**：通过特定参数支持非 OpenAI 原生模型
- **简单调用**：直接使用 langchain_openai.OpenAIEmbeddings 类进行调用

## 使用方法

### 1. 本地模型使用

```python
from local_embedding import load_embedding_model

# 加载本地模型
model_path = r'D:\project\model\bge_small_zh_v1.5'
embeddings = load_embedding_model(model_path, device="cpu")

# 单文本嵌入
result = embeddings.embed_query("你好")
print(f"嵌入向量长度: {len(result)}")

# 多文本嵌入
texts = ["文本1", "文本2", "文本3"]
results = embeddings.embed_documents(texts)
print(f"嵌入结果数量: {len(results)}")
```

### 2. 云端模型使用

```python
from cloud_embedding import CloudEmbeddings
import asyncio

# 创建云端嵌入实例
embeddings = CloudEmbeddings(
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="text-embedding-v4"
)

# 同步单文本嵌入
result = embeddings.embed_query("衣服的质量杠杠的")
print(f"嵌入向量长度: {len(result)}")

# 同步多文本嵌入
texts = ["衣服的质量很好", "这个产品很不错", "服务态度很好"]
results = embeddings.embed_documents(texts)
print(f"嵌入结果数量: {len(results)}")

# 异步单文本嵌入
async def async_example():
    result = await embeddings.aembed_query("衣服的质量杠杠的")
    print(f"异步嵌入向量长度: {len(result)}")
    
    results = await embeddings.aembed_documents(texts)
    print(f"异步嵌入结果数量: {len(results)}")

# 运行异步示例
asyncio.run(async_example())
```

### 3. 自定义云端 Embedding 服务

如果要封装其他云端 Embedding 服务，可以参考 CloudEmbeddings 类的实现，主要重写以下方法：

```python
from langchain_core.embeddings import Embeddings
from typing import List
import asyncio

class CustomEmbeddings(Embeddings):
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        # 初始化客户端
        pass
    
    def embed_query(self, text: str) -> List[float]:
        # 实现单文本嵌入
        pass
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 实现多文本嵌入
        pass
    
    async def aembed_query(self, text: str) -> List[float]:
        # 实现异步单文本嵌入
        pass
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        # 实现异步多文本嵌入
        pass
```

## 特性对比

| 特性 | 本地模型 | 云端模型 |
|------|---------|---------|
| 部署方式 | 本地部署 | 云端API |
| 初始成本 | 高（需要硬件） | 低（按使用付费） |
| 响应速度 | 快（无网络延迟） | 慢（受网络影响） |
| 可扩展性 | 受硬件限制 | 高可扩展 |
| 数据隐私 | 完全本地 | 需上传到云端 |
| 维护成本 | 高 | 低 |
| 模型选择 | 有限（需下载） | 丰富（云端提供） |

## 常见 Embedding 模型

### 本地模型
- **BGE 系列**：bge-small-zh-v1.5、bge-base-zh-v1.5、bge-large-zh-v1.5
- **Sentence-BERT**：all-MiniLM-L6-v2、all-mpnet-base-v2
- **多语言模型**：multilingual-MiniLM-L12-v2

### 云端服务
- **阿里云百炼**：text-embedding-v4、text-embedding-v3
- **OpenAI**：text-embedding-ada-002、text-embedding-3-small、text-embedding-3-large
- **智谱AI**：embedding-2
- **百度文心**：embedding-v1
