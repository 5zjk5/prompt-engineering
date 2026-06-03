# AI 热点分析系统

## 项目简介

基于 FastAPI 的 AI 新闻热点分析系统，通过多源搜索、智能筛选、内容聚合和趋势分析，自动生成 AI 行业热点报告。

## 核心流程

```mermaid
flowchart LR
    A[读取配置文件] --> B[生成搜索查询]
    B --> C[多引擎搜索]
    C --> D[置信度筛选]
    D --> E[网页内容爬取]
    E --> F[内容压缩聚合]
    F --> G[生成今日报告]
    G --> H[保存到数据库]
    H --> I[读取历史数据]
    I --> J[趋势对比分析]
    J --> K[输出最终结果]
    
    style A fill:#e1f5ff,stroke:#333,stroke-width:2px
    style G fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#9f9,stroke:#333,stroke-width:2px
    style J fill:#9f9,stroke:#333,stroke-width:2px
    style K fill:#ff9,stroke:#333,stroke-width:2px
```

## 详细流程说明

### 1. 初始化与配置读取
- 读取 `reference/news-url.txt` 获取预设新闻源链接
- 读取 `reference/news-query.txt` 获取查询模板
- 计算时间范围（过去24小时）

### 2. 智能查询生成
- 基于查询模板，使用大模型迭代生成搜索查询（默认3次）
- 每次迭代时将已生成的查询作为上下文，避免重复
- 最终去重得到唯一的查询列表

### 3. 多源搜索
- 使用 DuckDuckGo 和火山搜索两个搜索引擎
- 并发执行搜索任务（每批5个查询）
- 自动去重搜索结果

### 4. 智能链接筛选
- 批量处理搜索结果（每批50个）
- 使用大模型对每个搜索结果进行置信度打分（0-1）
- 过滤掉置信度低于阈值（默认0.7）的链接
- 保留高相关性链接用于后续处理

### 5. 网页内容获取
- 将链接分为两部分，分别使用 Coze Fetch 和 Jina Fetch
- 并发获取网页内容，提高效率
- 自动处理获取失败的链接

### 6. 内容压缩聚合
- 批量处理网页内容（每批10个）
- 使用大模型压缩网页内容，提取关键信息
- 保留时间范围内的相关内容

### 7. 报告生成
- 将压缩后的内容进行最终总结
- 生成今日 AI 行业热点报告

### 8. 数据持久化
- 将今日报告保存到 SQLite 数据库
- 数据库文件路径：`db/ai_today_news.db`
- 记录创建时间和内容

### 9. 趋势对比分析
- 从数据库读取过去7天的历史报告
- 对比今日报告与历史数据
- 生成趋势分析和洞察

## 项目结构

```
fastapi_server/
├── workflow/              # 业务流程模块
│   └── today_news.py     # 今日新闻核心逻辑
├── prompts/              # 提示词模板
│   └── today_news.py     # 各环节的提示词
├── tools/                # 工具模块
│   ├── search.py        # 搜索工具（DuckDuckGo、火山搜索）
│   └── fetch.py         # 网页抓取工具（Coze、Jina）
├── llm/                  # 大模型封装
│   └── ChatOpenAIModel_LangChian.py
├── utils/                # 工具函数
│   ├── logger.py        # 日志工具
│   └── llm_generation.py # LLM调用封装
├── reference/            # 配置文件
│   ├── news-url.txt     # 预设新闻源链接
│   └── news-query.txt   # 查询模板
├── db/                   # 数据库文件
│   └── ai_today_news.db
├── logs/                 # 日志文件
├── .env                  # 环境变量配置
├── main.py              # FastAPI 主程序
└── README.md            # 项目说明文档
```

## 环境配置

### 1. 安装依赖

```bash
pip install fastapi uvicorn python-dotenv langchain langchain-openai
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件，配置以下参数：

```env
# 火山搜索配置
COZE_API_TOKEN=your_coze_api_token
COZE_API_URL=https://api.coze.cn/v1/workflow/run
SEARCH_WORKFLOW_ID=your_search_workflow_id
FETCH_WORKFLOW_ID=your_fetch_workflow_id

# Jina Fetch 配置
JINA_API_TOKEN=your_jina_api_token

# LLM API 配置
LLM_API_KEY=your_llm_api_key
LLM_API_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=GLM-4-Flash-250414
EXTRA_BODY={"thinking": {"type": "disabled"}}
```

## 使用方法

### 启动服务

```bash
# 方式1：直接运行
python main.py

# 方式2：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 7396 --reload
```

### 访问接口

```bash
# 测试连接
curl http://localhost:7396/hello

# 获取今日新闻
curl http://localhost:7396/api/today_news
```

## 调试指南

### 1. 日志查看

日志文件保存在 `logs/` 目录，文件名格式：`YYYYMMDD_HH_MM_today_news.log`







