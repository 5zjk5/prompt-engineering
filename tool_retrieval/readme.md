# 工具检索系统 (Tool Retrieval System)

## 项目概述

工具检索系统是一个基于向量数据库和多种检索算法的工具管理平台，旨在提供高效的工具存储、检索和管理功能。系统支持工具的增删改查操作，并提供了多种检索方法，包括稠密检索、稀疏检索、关键词检索和混合检索，以满足不同场景下的工具检索需求。

## 核心思路

### 系统架构

系统采用微服务架构，主要包含以下几个核心组件：

1. **FastAPI服务层**：提供RESTful API接口，处理HTTP请求和响应
2. **向量数据库层**：使用ChromaDB存储工具的向量表示和假设性问题
3. **检索引擎层**：实现多种检索算法，包括稠密检索、稀疏检索、关键词检索和混合检索
4. **模型服务层**：集成大语言模型和嵌入模型，用于工具描述优化和向量化
5. **数据管理层**：处理工具的增删改查操作

### 检索原理

系统采用多模态检索策略，结合了以下几种检索方法：

1. **稠密检索（Dense Retrieval）**：
   - 使用嵌入模型将工具描述和查询转换为向量
   - 通过计算向量间的余弦相似度进行检索
   - 适合语义匹配，能够理解查询的深层含义

2. **稀疏检索（Sparse Retrieval）**：
   - 使用BM25算法进行关键词匹配
   - 基于词频统计，适合精确匹配关键词
   - 对专业术语和特定名称的检索效果较好

3. **关键词检索（Keyword Retrieval）**：
   - 使用TF-IDF算法进行关键词匹配
   - 基于词频和逆文档频率，适合一般性关键词检索
   - 计算简单，检索速度快

4. **混合检索（Hybrid Retrieval）**：
   - 结合多种检索方法的结果
   - 支持多种融合策略：自适应策略、排序融合、加权平均
   - 能够平衡不同检索方法的优缺点，提高检索准确率

### 工具优化流程

系统提供了工具描述优化功能，通过大语言模型对工具描述进行优化，使其更加清晰、准确和结构化，从而提高检索效果。同时，系统还会为每个工具生成假设性问题，用于增强检索的覆盖范围。

## 使用方法

### 环境准备

1. **安装依赖**：
```bash
pip install -r requirements.txt
```

2. **配置环境变量**：
   - 复制`.env`文件并根据实际情况修改配置
   - 主要配置项包括：
     - `API_KEY`：大语言模型API密钥
     - `BASE_URL`：大语言模型服务地址
     - `MODEL`：使用的大语言模型
     - `MODELSCOPE_API_KEY`：ModelScope API密钥
     - `EMBEDDING_MODEL`：嵌入模型名称

### 启动服务

```bash
python svs_service.py
```

服务将在`http://localhost:8009`启动，可以通过浏览器访问API文档。

### 批量导入工具

```bash
python insert_tools.py
```

该脚本会读取`data/tool.json`文件中的工具定义，并批量导入到系统中。

### 测试API

```bash
python test_single_api.py
```

该脚本提供了对各个API接口的测试功能。

### 评估检索效果

```bash
python eval_retrieval.py
```

该脚本会读取`data/query.xlsx`文件中的查询，并评估检索系统的准确率。

## 接口参数说明

### 1. 插入工具接口

**接口路径**：`POST /tools/insert_tool`

**请求参数**：
```json
{
  "tool_json": {
    "name": "工具名称",
    "description": "工具描述",
    "parameters": {
      "type": "object",
      "properties": {
        "参数名": {
          "type": "参数类型",
          "description": "参数描述"
        }
      },
      "required": ["必需参数列表"]
    }
  },
  "tool_optimized": true
}
```

**参数说明**：
- `tool_json`：工具的JSON定义，包含名称、描述和参数
- `tool_optimized`：是否优化工具描述，默认为true

**响应示例**：
```json
{
  "detail": "Insert tool success!"
}
```

### 2. 删除工具接口

**接口路径**：`POST /tools/delete_tool`

**请求参数**：
```json
{
  "tool_name": "工具名称"
}
```

**参数说明**：
- `tool_name`：要删除的工具名称

**响应示例**：
```json
{
  "detail": "Delete tool success!"
}
```

### 3. 更新工具接口

**接口路径**：`POST /tools/update_tool`

**请求参数**：
```json
{
  "tool_json": {
    "name": "工具名称",
    "description": "工具描述",
    "parameters": {
      "type": "object",
      "properties": {
        "参数名": {
          "type": "参数类型",
          "description": "参数描述"
        }
      },
      "required": ["必需参数列表"]
    }
  }
}
```

**参数说明**：
- `tool_json`：工具的JSON定义，包含名称、描述和参数

**响应示例**：
```json
{
  "detail": "Update tool success!"
}
```

### 4. 查询工具接口

**接口路径**：`POST /tools/select_tool`

**请求参数**：
```json
{
  "tool_name": "工具名称（可选）"
}
```

**参数说明**：
- `tool_name`：要查询的工具名称，如果为空则返回所有工具

**响应示例**：
```json
{
  "tools": [
    {
      "name": "工具名称",
      "description": "工具描述",
      "parameters": {
        "type": "object",
        "properties": {
          "参数名": {
            "type": "参数类型",
            "description": "参数描述"
          }
        },
        "required": ["必需参数列表"]
      }
    }
  ]
}
```

### 5. 检索工具接口

**接口路径**：`POST /tools/retrieval_tool`

**请求参数**：
```json
{
  "query": "检索查询",
  "method": "hybrid",
  "n_results": 5
}
```

**参数说明**：
- `query`：检索查询文本
- `method`：检索方法，可选值为"dense"、"sparse"、"hybrid"、"keyword"，默认为"hybrid"
- `n_results`：返回结果数量，默认为5

**响应示例**：
```json
{
  "results": [
    {
      "tool_id": "工具名称",
      "score": 0.95,
      "metadata": {},
      "document": "工具JSON字符串",
      "collection": "tool_vector",
      "score_type": "hybrid",
      "method_scores": {
        "dense": 0.9,
        "sparse": 0.8,
        "keyword": 0.7
      },
      "raw_method_scores": {
        "dense": 0.9,
        "sparse": 25.6,
        "keyword": 0.7
      }
    }
  ]
}
```

## 文件目录结构

```
tool_retrieval/
├── .env                          # 环境变量配置文件
├── .vscode/                      # VSCode配置目录
│   └── launch.json               # VSCode启动配置
├── __pycache__/                  # Python缓存目录
├── data/                         # 数据目录
│   ├── query.xlsx                # 查询测试数据
│   └── tool.json                 # 工具定义数据
├── db/                          # 数据库目录
│   ├── [UUID]/                   # ChromaDB集合数据目录
│   │   ├── data_level0.bin       # 数据文件
│   │   ├── header.bin            # 头文件
│   │   ├── length.bin            # 长度文件
│   │   └── link_lists.bin        # 链表文件
│   ├── cache/                    # 缓存目录
│   └── chroma.sqlite3           # ChromaDB主数据库文件
├── db_operation/                 # 数据库操作模块
│   ├── __init__.py               # 模块初始化文件
│   ├── delete.py                 # 删除操作实现
│   ├── insert.py                 # 插入操作实现
│   ├── select.py                 # 查询操作实现
│   └── update.py                 # 更新操作实现
├── eval_retrieval-res.xlsx       # 检索评估结果
├── eval_retrieval.py             # 检索评估脚本
├── insert_tools.py              # 批量插入工具脚本
├── logs/                        # 日志目录
│   ├── [YYYY-MM-DD]/             # 按日期分组的日志目录
│   │   ├── delete_YYYY-MM-DD.log # 删除操作日志
│   │   ├── insert_YYYY-MM-DD.log # 插入操作日志
│   │   ├── retrieval_YYYY-MM-DD.log # 检索操作日志
│   │   ├── select_YYYY-MM-DD.log # 查询操作日志
│   │   └── update_YYYY-MM-DD.log # 更新操作日志
│   └── logger.py                 # 日志配置模块
├── model.py                     # 数据模型定义
├── svs_service.py               # 主服务文件
├── test_single_api.py           # 单个API测试脚本
└── utils/                       # 工具模块
    ├── embedding_api.py         # 嵌入模型API封装
    ├── llm_api.py               # 大语言模型API封装
    ├── retrieval.py             # 检索功能实现
    └── utils.py                 # 通用工具函数
```

## 各文件功能说明

### 核心服务文件

- **svs_service.py**：主服务文件，定义了FastAPI应用和所有API接口
- **model.py**：定义了API请求和响应的数据模型
- **db_operation/__init__.py**：定义了数据库生命周期管理函数

### 数据库操作文件

- **db_operation/insert.py**：实现工具插入功能，包括工具描述优化和假设性问题生成
- **db_operation/delete.py**：实现工具删除功能
- **db_operation/update.py**：实现工具更新功能
- **db_operation/select.py**：实现工具查询功能

### 检索功能文件

- **utils/retrieval.py**：实现多种检索算法，包括稠密检索、稀疏检索、关键词检索和混合检索
- **utils/embedding_api.py**：封装嵌入模型API，用于文本向量化
- **utils/llm_api.py**：封装大语言模型API，用于工具描述优化和假设性问题生成

### 工具和辅助文件

- **utils/utils.py**：提供通用工具函数，如工具验证和JSON解析
- **logs/logger.py**：定义日志记录器配置，支持按日期和操作类型分组记录日志
- **insert_tools.py**：批量插入工具的脚本
- **test_single_api.py**：测试单个API接口的脚本
- **eval_retrieval.py**：评估检索系统准确率的脚本

### 数据文件

- **data/tool.json**：包含多个工具的JSON定义，用于批量导入
- **data/query.xlsx**：包含测试查询和标准答案，用于评估检索效果

## 检索方法

### 1. 稠密检索（Dense Retrieval）

稠密检索使用嵌入模型将工具描述和查询转换为向量，通过计算向量间的余弦相似度进行检索。这种方法能够理解查询的深层含义，适合语义匹配。

**实现原理**：
1. 使用嵌入模型将查询文本转换为向量
2. 在工具向量集合中执行向量检索
3. 在假设性问题集合中执行向量检索
4. 合并两个集合的检索结果并按相似度排序
5. 根据工具名去重并返回前N个结果

**适用场景**：
- 查询与工具描述语义相似但关键词不匹配的情况
- 需要理解查询意图的场景
- 查询较长或描述性较强的情况

### 2. 稀疏检索（Sparse Retrieval）

稀疏检索使用BM25算法进行关键词匹配，基于词频统计，适合精确匹配关键词。这种方法对专业术语和特定名称的检索效果较好。

**实现原理**：
1. 对所有文档进行分词
2. 使用BM25算法构建索引
3. 对查询进行分词并计算BM25分数
4. 按分数排序并返回前N个结果
5. 根据工具名去重

**适用场景**：
- 查询包含特定专业术语或名称的情况
- 需要精确匹配关键词的场景
- 查询较短且关键词明确的情况

### 3. 关键词检索（Keyword Retrieval）

关键词检索使用TF-IDF算法进行关键词匹配，基于词频和逆文档频率，适合一般性关键词检索。这种方法计算简单，检索速度快。

**实现原理**：
1. 使用TF-IDF向量化器对所有文档进行向量化
2. 对查询进行向量化
3. 计算查询与文档的余弦相似度
4. 按相似度排序并返回前N个结果
5. 根据工具名去重

**适用场景**：
- 一般性关键词检索
- 需要快速响应的场景
- 查询包含常见关键词的情况

### 4. 混合检索（Hybrid Retrieval）

混合检索结合多种检索方法的结果，支持多种融合策略，能够平衡不同检索方法的优缺点，提高检索准确率。

**实现原理**：
1. 串行执行多种检索方法（稠密、稀疏、关键词）
2. 合并各方法的检索结果
3. 根据选择的融合策略计算最终分数：
   - **自适应策略**：根据查询长度和内容动态调整权重
   - **排序融合**：使用倒数排名融合（Reciprocal Rank Fusion）
   - **加权平均**：使用预设权重对各方法分数进行加权平均
4. 按最终分数排序并返回前N个结果
5. 根据工具名去重

**适用场景**：
- 需要综合多种检索方法的优点的场景
- 查询类型多样或不确定的情况
- 对检索准确率要求较高的场景

## 模型配置

### 大语言模型配置

系统使用大语言模型进行工具描述优化和假设性问题生成。模型配置通过环境变量进行设置：

```env
# 智谱 GLM 大模型配置
API_KEY=您的API密钥
BASE_URL=https://open.bigmodel.cn/api/paas/v4/
MODEL=glm-4.5-flash

# 或者使用 Modelscope 大模型配置
API_KEY=您的API密钥
BASE_URL=https://api-inference.modelscope.cn/v1
MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507
```

**配置说明**：
- `API_KEY`：大语言模型服务的API密钥
- `BASE_URL`：大语言模型服务的访问地址
- `MODEL`：使用的大语言模型名称

### 嵌入模型配置

系统使用嵌入模型将文本转换为向量，用于稠密检索。模型配置通过环境变量进行设置：

```env
# modelscope 配置
MODELSCOPE_API_KEY=您的API密钥
EMBEDDING_MODEL=tongyi-embedding-vision-plus
```

**配置说明**：
- `MODELSCOPE_API_KEY`：ModelScope服务的API密钥
- `EMBEDDING_MODEL`：使用的嵌入模型名称

### 模型选择建议

1. **大语言模型选择**：
   - 如果需要中文支持，推荐使用`glm-4-5-flash`或`Qwen/Qwen3-235B-A22B-Instruct-2507`
   - 如果需要英文支持，可以考虑使用GPT系列模型
   - 如果需要多语言支持，可以考虑使用多语言模型

2. **嵌入模型选择**：
   - 如果需要中文支持，推荐使用`tongyi-embedding-vision-plus`或`multimodal-embedding-v1`
   - 如果需要英文支持，可以考虑使用OpenAI的嵌入模型
   - 如果需要多语言支持，可以考虑使用多语言嵌入模型

## 性能优化

### 检索性能优化

1. **缓存机制**：
   - 系统使用缓存目录存储中间结果，减少重复计算
   - 缓存目录位于`db/cache`，系统会自动创建和管理

2. **并行处理**：
   - 混合检索中各方法串行执行，避免资源竞争
   - 批量处理工具时，每个工具独立处理，提高并发性

3. **结果去重**：
   - 所有检索方法都会根据工具名进行去重，避免重复结果
   - 去重过程保留分数最高的结果，确保检索质量

### 数据库性能优化

1. **向量索引**：
   - ChromaDB自动为向量数据创建索引，提高检索效率
   - 索引数据存储在`db/[UUID]`目录下

2. **集合分离**：
   - 工具向量和假设性问题存储在不同的集合中，提高检索效率
   - 工具向量存储在`tool_vector`集合中
   - 假设性问题存储在`hypothetical_query`集合中

### 日志管理优化

1. **日志分级**：
   - 控制台日志级别为INFO，文件日志级别为DEBUG
   - 不同操作类型使用不同的日志记录器，便于管理和排查问题

2. **日志轮转**：
   - 日志按日期分组存储，便于历史查询和管理
   - 每个操作类型每天生成一个日志文件

## 扩展功能

### 自定义检索方法

系统支持自定义检索方法，可以通过以下步骤添加新的检索方法：

1. 在`utils/retrieval.py`中的`RetrievalService`类中添加新的检索方法
2. 在`retrieval_tool_func`函数中添加对新方法的支持
3. 更新API接口文档，说明新方法的参数和用法

### 自定义融合策略

系统支持自定义混合检索的融合策略，可以通过以下步骤添加新的融合策略：

1. 在`utils/retrieval.py`中的`hybrid_retrieval`方法中添加新的策略逻辑
2. 更新API接口文档，说明新策略的参数和用法

### 自定义嵌入模型

系统支持自定义嵌入模型，可以通过以下步骤添加新的嵌入模型：

1. 在`utils/embedding_api.py`中添加对新模型的支持
2. 更新环境变量配置，添加新模型的配置项
3. 更新文档，说明新模型的配置方法和使用注意事项

## 常见问题

### 1. 如何添加新工具？

可以通过以下两种方式添加新工具：

1. **使用API接口**：
   - 调用`POST /tools/insert_tool`接口
   - 提供工具的JSON定义
   - 设置`tool_optimized`参数控制是否优化工具描述

2. **批量导入**：
   - 在`data/tool.json`文件中添加工具定义
   - 运行`python insert_tools.py`脚本批量导入

### 2. 如何优化检索效果？

可以通过以下几种方式优化检索效果：

1. **优化工具描述**：
   - 确保工具描述清晰、准确、结构化
   - 包含工具的核心功能和关键参数
   - 避免冗余和模糊的描述

2. **选择合适的检索方法**：
   - 根据查询特点选择合适的检索方法
   - 对于语义查询，使用稠密检索
   - 对于关键词查询，使用稀疏检索或关键词检索
   - 对于复杂查询，使用混合检索

3. **调整混合检索参数**：
   - 根据查询特点选择合适的融合策略
   - 调整各检索方法的权重
   - 适当增加返回结果数量

### 3. 如何处理检索失败？

检索失败可能由以下原因导致，可以按以下方式处理：

1. **检查服务状态**：
   - 确保服务正常运行
   - 检查数据库连接是否正常

2. **检查查询内容**：
   - 确保查询内容不为空
   - 避免使用特殊字符和敏感词

3. **检查模型配置**：
   - 确保API密钥正确配置
   - 检查模型服务是否可用

4. **查看日志信息**：
   - 检查`logs`目录下的日志文件
   - 根据错误信息排查问题

### 4. 如何提高系统性能？

可以通过以下几种方式提高系统性能：

1. **优化硬件配置**：
   - 增加内存容量
   - 使用高性能存储设备
   - 确保网络连接稳定

2. **调整检索参数**：
   - 适当减少返回结果数量
   - 选择合适的检索方法
   - 避免不必要的检索操作

3. **定期维护数据库**：
   - 清理无用的数据
   - 重建索引
   - 优化数据库配置
