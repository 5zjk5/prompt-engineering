# DeepSearch Go版本

DeepSearch Go版本是基于GLM-4.5-flash的深度搜索引擎的Go语言实现，提供主题拆解、搜索执行、结果筛选等完整功能。

## 项目结构

```
deep_search-dev-go/
├── api/                    # API模块
│   ├── llm_api.go         # 大语言模型API
│   ├── search_api.go      # 搜索API
│   └── crawler_api.go    # 爬虫API
├── deepsearch/            # 深度搜索核心模块
│   ├── main_deepsearch.go # 深度搜索主逻辑
│   ├── main_search.go     # 搜索和爬取逻辑
│   ├── utils/             # 工具函数
│   │   ├── utils.go       # 通用工具函数
│   │   └── parse_data.go  # 数据解析和保存
│   └── prompt/            # 提示词模板
│       ├── formulate_query.go    # 查询生成提示词
│       ├── related_url.go       # URL相关性判断提示词
│       ├── summary_crawl_res.go # 内容总结提示词
│       ├── final_summary.go     # 最终总结提示词
│       └── prompt_lang.go       # 提示词管理
├── logs/                  # 日志模块
│   └── logger.go          # 日志记录实现
├── eval/                  # 评估数据目录
│   └── deepsearch_data/   # 深度搜索数据
├── .env                   # 环境变量配置
├── go.mod                 # Go模块定义
├── go.sum                 # Go依赖校验
├── readme.md              # 项目说明文档
└── svs_deepsearch.go      # 主服务入口
```

## 功能特点

1. **主题拆解**：将复杂主题拆解为多个精准的搜索查询
2. **智能搜索**：执行搜索并获取相关结果
3. **结果筛选**：从搜索结果中选择最相关的URL
4. **内容爬取**：爬取选定URL的内容
5. **结果总结**：对爬取内容进行智能总结
6. **最终汇总**：生成全面、深入的最终研究报告
7. **取消支持**：支持取消正在进行的搜索任务

## 安装与配置

### 1. 环境要求

- Go 1.21或更高版本
- 网络连接（用于调用API和爬取网页）

### 2. 初始化项目

```bash
# 初始化Go模块
go mod init deepsearch
go mod tidy
```

### 3. 环境变量配置

在项目根目录创建`.env`文件，配置必要的环境变量：

```
# GLM API配置
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 搜索API配置
SEARCH_API_KEY=your_search_api_key
SEARCH_API_URL=https://api.search.com/v1/search

# 其他配置
LOG_LEVEL=info
PORT=7396
```

## 使用方法

### 1. 启动服务

```bash
# 运行主服务
go run svs_deepsearch.go
```

服务将在7396端口启动。

### 2. 调用API

发送POST请求到`/api/deep_search`端点：

```bash
curl -X POST http://localhost:7396/api/deep_search \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能的发展趋势", "mode": "deepsearch"}'
```

### 3. 响应格式

成功响应：
```json
{
  "status": 200,
  "time": 45.67,
  "msg": "success",
  "data": "深度搜索结果内容..."
}
```

错误响应：
```json
{
  "status": 500,
  "msg": "fail",
  "data": "错误信息"
}
```

## API文档

### 深度搜索API

**端点**: `POST /api/deep_search`

**请求参数**:
- `topic` (string, 必需): 搜索主题
- `mode` (string, 可选): 搜索模式，默认为"deepsearch"

**响应**:
- `status` (int): HTTP状态码
- `time` (float): 请求处理时间（秒）
- `msg` (string): 响应消息
- `data` (string): 深度搜索结果

### 健康检查API

**端点**: `GET /health`

**响应**:
```json
{
  "status": "ok",
  "message": "服务正常运行"
}
```

## 开发指南

### 1. 添加新功能

1. 在相应模块中添加新功能
2. 更新API文档
3. 添加单元测试
4. 提交代码并创建Pull Request

### 2. 代码规范

- 遵循Go语言官方代码规范
- 使用有意义的变量和函数名
- 添加适当的注释
- 处理错误情况

### 3. 日志记录

使用日志模块记录重要信息：

```go
logger := logs.DefineLogLevel("info", "module_name")
logger.Info("信息日志")
logger.Warning("警告日志")
logger.Error("错误日志")
logger.Debug("调试日志")
```

## 常见问题

### 1. 如何配置API密钥？

在项目根目录的`.env`文件中配置API密钥：

```
GLM_API_KEY=your_glm_api_key
SEARCH_API_KEY=your_search_api_key
```

### 2. 如何修改日志级别？

在`.env`文件中设置`LOG_LEVEL`变量：

```
LOG_LEVEL=debug  # 可选值: debug, info, warning, error
```

### 3. 如何自定义提示词模板？

在`deepsearch/prompt`目录下修改相应的提示词模板文件。

## 许可证

本项目采用MIT许可证，详情请参阅LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来贡献代码。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件至项目维护者