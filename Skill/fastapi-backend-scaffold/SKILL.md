---
name: fastapi-backend-scaffold
description: 生成标准 FastAPI 后端分层架构目录脚手架。当用户需要从零搭建 FastAPI 后端、重构后端目录结构、或创建新的后端项目时触发此技能。技能内置 LLM 多模型客户端（支持重试、流式、备用切换）、会话级日志、SQLite 数据访问层、SSE 流式 API 示例等生产级模板代码，一键生成完整可运行的后端骨架。触发场景包括"搭建后端"、"创建 FastAPI 项目"、"重构后端架构"、"生成后端目录"等。
agent_created: true
---

# FastAPI Backend Scaffold

## 概述

本技能用于生成标准 FastAPI 后端分层架构目录脚手架。架构源自生产级 ChatExcel 项目，经过实际验证，包含多模型容错、会话级日志、SSE 流式响应等生产级特性。

生成的后端采用清晰的分层架构：`core`（基础设施）→ `llm`（模型客户端）→ `dal`（数据访问）→ `services`（业务逻辑）→ `api`（路由层），职责边界清晰，易于扩展。

## 何时使用

在以下场景触发本技能：

- 用户要求从零搭建一个 FastAPI 后端项目
- 用户要求重构现有后端的目录结构
- 用户要求创建新的后端服务，需要标准目录结构
- 用户要求生成后端脚手架 / 骨架代码

典型触发语：
- "帮我搭建一个 FastAPI 后端"
- "创建一个后端项目"
- "重构后端目录结构"
- "生成后端脚手架"
- "从头写一个后端"

## 生成的目录结构

```
backend/
├── main.py                      # FastAPI 入口（路由注册、中间件、启动事件）
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── app/
│   ├── __init__.py
│   ├── core/                    # 核心基础设施层
│   │   ├── __init__.py
│   │   ├── config.py            # 全局配置（.env 驱动）
│   │   └── logger.py            # 会话级日志（每会话独立文件）
│   ├── llm/                     # LLM 客户端层（直接照抄，不修改）
│   │   ├── __init__.py
│   │   ├── client.py            # OpenAI 兼容客户端（多模型、重试、流式）
│   │   └── llm_config.py        # 多模型配置管理
│   ├── dal/                     # 数据访问层
│   │   ├── __init__.py
│   │   └── database.py          # SQLite 连接与表初始化
│   ├── api/                     # API 路由层
│   │   ├── __init__.py
│   │   └── example.py           # SSE 流式对话示例
│   ├── services/                # 业务逻辑层
│   │   └── __init__.py
│   └── prompts/                 # 提示词管理
│       └── __init__.py
├── logs/                        # 日志目录（运行时自动创建子目录）
├── skills/                      # 技能目录
└── storage/                     # 存储目录（按需存放项目文件，结构由实际需求决定）
```

## 执行流程

### 第一步：确认目标目录

向用户确认后端代码要生成到哪个目录。如果用户未指定，默认建议在当前项目根目录下创建 `backend/` 目录。

### 第二步：运行脚手架脚本

执行 `scripts/scaffold.py` 生成完整目录结构：

```bash
python <技能目录>/scripts/scaffold.py <目标目录> [--project-name <项目名称>]
```

示例：
```bash
python scripts/scaffold.py ./backend --project-name "My API"
```

脚本会自动完成：
1. 复制 LLM 模块到 `app/llm/`（直接照抄，不做修改）
2. 复制 core 模块模板（config.py、logger.py）
3. 复制 dal 模块模板（database.py）
4. 生成 api 模块（含 SSE 流式示例）
5. 创建 services、prompts 空模块
6. 生成 main.py 入口、requirements.txt、.env.example
7. 创建 logs、skills、storage 顶层运行时目录

> **注意**：不生成 `.gitignore` 和 `.gitkeep` 文件。`storage/` 仅创建顶层目录，
> 不预生成子目录结构，由运行时代码按需自动创建。

### 第三步：指导用户完成配置

脚手架生成后，告知用户后续步骤：

1. 安装依赖：`pip install -r requirements.txt`
2. 复制环境变量：`cp .env.example .env` 并按需修改
3. **配置模型服务**：修改 `app/llm/llm_config.py` 中的 `LLM_PROVIDERS` 列表，填入实际的模型 base_url、api_key、model 名称
4. 启动服务：`python main.py`

## LLM 模块说明（必须照抄，不修改）

> **强制要求**：只要使用了本技能，`app/llm/` 模块**必须**使用本技能提供的模板代码（包含多模型备用切换、失败重试、流式安全重试等逻辑）。
> 即便目标项目已有 LLM 相关代码，也必须替换为本技能的模板，以确保具备自动切换和重试能力。
> 除非用户明确说明不需要这些能力，否则一律按模板生成。

`app/llm/` 目录是从生产项目直接照抄的参考模板代码，包含以下核心能力：

### client.py — 统一调用接口

提供 4 个核心函数：

| 函数 | 用途 | 返回值 |
|------|------|--------|
| `chat_completion()` | 非流式调用，返回原始 response | OpenAI Response 对象 |
| `chat_completion_stream()` | 流式调用 | `AsyncIterator[str]` |
| `chat_completion_full()` | 非流式调用，返回完整文本 | `str` |
| `count_tokens()` | token 估算 | `int` |

### llm_config.py — 多模型配置

在 `LLM_PROVIDERS` 列表中集中配置所有模型服务。重试时按顺序自动轮换 provider。

关键特性：
- **多模型备用切换**：配置多个 provider，重试时轮换
- **超时控制**：非流式 60s，流式首 chunk 10s（可由环境变量调整）
- **异常分类**：超时/连接错误/限流可重试，4xx 不可重试
- **流式安全重试**：首个内容 chunk 超时才重试，已开始输出后不重试

### 使用示例

```python
from app.llm.client import chat_completion_stream, chat_completion_full

# 流式调用
async for chunk in chat_completion_stream(
    messages=[{"role": "user", "content": "你好"}],
):
    print(chunk, end="", flush=True)

# 非流式调用
result = await chat_completion_full(
    messages=[{"role": "user", "content": "总结这段话"}],
)
```

## 其他模块说明

### core/config.py — 全局配置

所有配置从 `.env` 读取，集中在文件顶部定义。目录路径基于 `__file__` 相对计算，不依赖工作目录。模块加载时自动创建所需目录。

### core/logger.py — 会话级日志

每个 `conv_uid` 生成独立日志文件，路径为 `logs/user/{module}/{conv_uid}.log`。

```python
from app.core.logger import get_session_logger

logger = get_session_logger(conv_uid, "chat")
logger.info("用户输入: %s", user_input)
```

### dal/database.py — SQLite 数据访问

使用 aiosqlite 异步驱动。`get_db()` 返回连接，调用方负责关闭。

### api/example.py — SSE 流式 API 示例

演示标准的 SSE 流式对话接口写法，包含异常处理和事件格式。

### storage/ — 文件存储

`storage/` 目录用于存放项目运行时所需的文件，例如数据库文件、用户上传的文件、临时文件、静态资源等。
脚手架仅创建顶层 `storage/` 目录，**不预生成任何子目录结构**——具体的目录划分由实际业务需求决定，
运行时代码（如 `config.py` 中的 `os.makedirs`）会按需自动创建所需子目录。

## 架构详情

如需了解完整的架构设计细节、分层职责、关键设计模式，参考 `references/architecture.md`。

## 扩展指南

脚手架生成后，按以下方式扩展业务模块：

1. **新增 API 路由**：在 `app/api/` 下创建新文件，定义 `APIRouter`，在 `main.py` 中注册
2. **新增业务引擎**：在 `app/services/` 下按模块创建目录，编写引擎类
3. **新增提示词**：在 `app/prompts/` 下创建文件，包含系统提示常量、模板、构建函数
4. **新增数据表**：在 `app/dal/database.py` 的 `init_db()` 中添加建表 SQL，或创建新的 DAO 文件
5. **新增上传目录分层**：按 `{user}/{module}/{conv_uid}/` 结构在上传逻辑中创建目录
