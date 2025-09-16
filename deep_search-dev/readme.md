# DeepSearch - 深度搜索引擎

DeepSearch是一个基于大语言模型的智能深度搜索引擎，能够对用户提出的主题进行多轮迭代搜索、爬取和分析，最终生成全面、深入的总结报告。

使用大模型为智谱的 GLM-4.5-flash

## 项目概述

DeepSearch通过以下步骤实现深度搜索：

1. **主题拆解**：将用户输入的主题拆解为多个相关子查询
2. **搜索执行**：对每个子查询执行搜索，获取相关结果
3. **结果筛选**：使用大模型从搜索结果中筛选最相关的URL
4. **内容爬取**：爬取筛选后的URL内容
5. **内容评估**：评估爬取内容是否足够回答主题
6. **迭代优化**：如果内容不足，继续下一轮搜索
7. **最终总结**：将所有轮次的搜索结果汇总，生成最终总结

## 项目结构

```
deep_search-dev/
├── api/                    # API接口模块
│   ├── __init__.py
│   ├── crawler_api.py      # 网页爬取API
│   ├── llm_api.py          # 大语言模型API
│   └── search_api.py       # 搜索API
├── deepsearch/             # 深度搜索核心逻辑
│   ├── __init__.py
│   ├── main_deepsearch.py  # 深度搜索主逻辑
│   ├── main_search.py      # 搜索和爬取逻辑
│   ├── prompt/             # 提示词模板
│   │   ├── __init__.py
│   │   ├── final_summary.py
│   │   ├── formulate_query.py
│   │   ├── prompt_lang.py
│   │   ├── related_url.py
│   │   └── summary_cralw_res.py
│   └── utils/              # 工具函数
│       ├── __init__.py
│       ├── parse_data.py
│       └── utils.py
├── eval/                   # 评估数据存储
│   └── deepsearch_data/
├── logs/                   # 日志文件
│   ├── logger.py
│   └── logs/
├── .env                    # 环境变量配置
├── README.md               # 项目说明文档
├── svs_deepsearch.py       # FastAPI服务入口
├── test_crawler_api.py     # 爬虫API测试
├── test_deepsearch_api.py  # 深度搜索API测试
├── test_llm_api.py         # 大模型API测试
└── test_search_api.py      # 搜索API测试
```

## 核心模块说明

### 1. API模块 (api/)

#### LLM API (api/llm_api.py)
- **功能**：提供大语言模型接口，支持模型调用和请求取消
- **主要类**：`LLM`
- **关键方法**：
  - `infer(prompt, enable_thinking=False, temperature=0.7)`：调用大模型生成回复
  - `cancel_request()`：取消当前请求

#### Search API (api/search_api.py)
- **功能**：提供搜索接口，调用外部搜索服务获取结果
- **主要类**：`SearchAPI`
- **关键方法**：
  - `search(user_input)`：执行搜索操作
  - `format_search_results(results)`：格式化搜索结果

#### Crawler API (api/crawler_api.py)
- **功能**：提供网页爬取接口，使用Playwright进行浏览器自动化
- **主要类**：`CrawlerAPI`
- **关键方法**：
  - `init_browser()`：初始化浏览器
  - `close_browser()`：关闭浏览器
  - `crawl_single_url(url)`：爬取单个URL
  - `crawl_urls(urls)`：并行爬取多个URL

### 2. 深度搜索核心逻辑 (deepsearch/)

#### 主搜索逻辑 (deepsearch/main_deepsearch.py)
- **功能**：实现深度搜索的主要流程控制
- **主要类**：`DeepSearch`
- **关键方法**：
  - `run()`：执行深度搜索主流程
  - `step_formulate_query(ephos)`：拆解主题为子查询
  - `step_search_crawl(rewrite_query)`：搜索和爬取内容
  - `step_summarize_crawl_res(crawl_res)`：总结爬取结果
  - `step_final_summary()`：生成最终总结

#### 搜索和爬取逻辑 (deepsearch/main_search.py)
- **功能**：实现搜索、URL筛选和内容爬取
- **主要类**：`SearchCrawl`
- **关键方法**：
  - `run()`：执行搜索和爬取流程
  - `select_related_url(serach_res_list, logger)`：选择相关URL

#### 工具函数 (deepsearch/utils/)
- **功能**：提供各种辅助功能
- **关键函数**：
  - `formulate_query(topic, have_query, summary_search, logger, query_num=5)`：根据主题规划查询
  - `summarize_crawl_res(crawl_res, topic, summary_search, logger)`：总结爬取结果
  - `final_summary(topic, summary_search, logger)`：生成最终总结

#### 提示词模板 (deepsearch/prompt/)
- **功能**：定义与大模型交互的提示词模板
- **主要文件**：
  - `formulate_query.py`：主题拆解提示词
  - `related_url.py`：URL选择提示词
  - `summary_cralw_res.py`：内容总结提示词
  - `final_summary.py`：最终总结提示词

## 环境配置

### 环境变量

项目使用`.env`文件配置环境变量，主要包含以下配置：

```env
# GLM Model Configuration
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_MODEL=glm-4.5-flash

# Search API Configuration
SEARCH_API_TOKEN=your_search_api_token
SEARCH_API_URL=https://api.coze.cn/v1/workflow/run
WORKFLOW_ID=your_workflow_id
```

### 依赖安装

项目依赖的主要Python包包括：

- `fastapi`：Web框架
- `uvicorn`：ASGI服务器
- `playwright`：浏览器自动化
- `openai`：OpenAI API客户端
- `python-dotenv`：环境变量加载
- `requests`：HTTP请求
- `aiohttp`：异步HTTP客户端
- `art`：ASCII艺术字生成

## 使用方法

### 1. 启动服务

```bash
python svs_deepsearch.py
```

服务将在 `http://localhost:7396` 启动。

### 2. API调用

#### 深度搜索API

**端点**：`POST /api/deep_search`

**请求参数**：
```json
{
    "topic": "最近医疗大健康有什么新动态，对创业者，个人有什么机遇？"
}
```

**响应示例**：
```json
{
    "status": 200,
    "time": 45.67,
    "msg": "success",
    "data": {
        "status": "success",
        "topic": "最近医疗大健康有什么新动态，对创业者，个人有什么机遇？",
        "have_query": ["2024年医疗大健康行业新动态 创业机遇", "人工智能在医疗大健康领域的最新应用 个人创业机会", ...],
        "summary_search": ["新知识提供了医疗大健康行业的最新动态，包括市场规模、消费者需求变化...", ...],
        "iter_num": 2,
        "deepsearch_summary_text": "# 医疗大健康行业新动态与创业机遇分析\n\n## 一、行业最新动态\n\n### 1. 市场规模与增长\n\n医疗大健康行业近年来保持稳定增长..."
    }
}
```

### 3. 测试

项目提供了多个测试文件，可以单独测试各个模块：

```bash
# 测试大模型API
python test_llm_api.py

# 测试搜索API
python test_search_api.py

# 测试爬虫API
python test_crawler_api.py

# 测试深度搜索API
python test_deepsearch_api.py
```

## 工作流程

1. **用户输入主题**：用户提供一个需要深度探索的主题
2. **主题拆解**：系统将主题拆解为多个相关子查询
3. **多轮搜索**：
   - 对每个子查询执行搜索
   - 使用大模型筛选最相关的URL
   - 爬取URL内容
   - 评估内容是否足够回答主题
   - 如果不足，继续下一轮搜索
4. **最终总结**：将所有轮次的搜索结果汇总，生成最终总结
5. **结果返回**：将最终总结返回给用户

## 日志系统

项目使用Python的logging模块实现日志系统，日志文件存储在`logs/logs/`目录下，按日期分类。

日志格式：
```
时间戳 - 日志级别 - [文件名:函数名:行号] - 日志内容
```

## 评估数据

项目会将每次深度搜索的中间数据和最终结果保存在`eval/deepsearch_data/`目录下，文件名格式为`{主题前30位}_{日期时间}.json`。

保存的数据包括：
- 主题
- 拆解的子查询
- 各轮次的搜索总结
- 最终总结
- 爬取的原始结果
- 搜索轮次

## 注意事项

1. **API密钥**：使用前需要配置有效的API密钥
2. **网络环境**：确保网络可以访问大模型API和搜索API
3. **浏览器依赖**：爬虫功能需要Playwright浏览器支持，首次使用时可能需要下载浏览器
4. **资源消耗**：深度搜索可能消耗较多计算资源和API配额
5. **超时设置**：各模块都有超时设置，可根据实际需求调整

## 扩展开发

项目设计为模块化结构，可以方便地扩展：

1. **添加新的LLM支持**：在`api/llm_api.py`中添加新的模型支持
2. **添加新的搜索源**：在`api/search_api.py`中添加新的搜索API
3. **修改提示词**：在`deepsearch/prompt/`目录下修改相应的提示词模板
4. **添加新的评估维度**：在`deepsearch/prompt/summary_cralw_res.py`中添加新的评估标准

