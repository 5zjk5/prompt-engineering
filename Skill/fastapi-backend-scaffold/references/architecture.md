# FastAPI 后端分层架构参考

## 架构总览

```
backend/
├── main.py                      # FastAPI 入口：路由注册、中间件、启动事件
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── app/
│   ├── core/                    # 核心基础设施层
│   │   ├── config.py            # 全局配置，.env 驱动
│   │   └── logger.py            # 会话级日志，每个会话独立文件
│   ├── llm/                     # LLM 客户端层（直接照抄，不修改）
│   │   ├── client.py            # OpenAI 兼容客户端，多模型、重试、流式
│   │   └── llm_config.py        # 多模型配置管理
│   ├── dal/                     # 数据访问层
│   │   ├── database.py          # SQLite 连接与表初始化
│   │   └── conversation.py      # 对话 CRUD（按需创建）
│   ├── api/                     # API 路由层
│   │   ├── upload.py            # 文件上传
│   │   ├── chat.py              # SSE 流式对话
│   │   └── conversation.py      # 对话管理 CRUD
│   ├── services/                # 业务逻辑层
│   │   └── {module}/            # 按业务模块分目录
│   │       ├── engine.py        # 引擎主逻辑
│   │       └── reader.py        # 数据读取器（按需）
│   └── prompts/                 # 提示词管理
│       └── {module}.py          # 按模块组织提示词
├── logs/                        # 运行时日志（运行时自动创建子目录）
│   └── user/
│       └── {module}/
├── skills/                      # 技能目录
└── storage/                     # 运行时存储（按需存放项目文件，结构由实际需求决定）
    └── ...                      # 子目录由业务需求决定，运行时代码按需创建
```

## 分层职责

### 1. core/ — 核心基础设施层

提供全局基础能力，不含业务逻辑。

- **config.py**: 所有配置从 `.env` 读取，集中在文件顶部定义。目录路径基于 `__file__` 相对计算，不依赖工作目录。
- **logger.py**: 会话级日志，每个 `conv_uid` 生成独立日志文件，路径为 `logs/user/{module}/{conv_uid}.log`。日志格式统一为 `时间 | 级别 | 文件:行号 | 函数名() | 消息`。

### 2. llm/ — LLM 客户端层（必须照抄）

封装大模型调用，对外暴露统一接口。**只要使用了本技能，此模块必须使用模板代码**（包含多模型备用切换、失败重试、流式安全重试），即便项目已有 LLM 代码也须替换，除非用户明确说明不需要。

- **client.py**: 提供 4 个核心函数，所有 `chat_completion*` 函数均支持可选 `logger` 参数：
  - `chat_completion()` — 非流式调用，返回原始 response（使用 `asyncio.wait_for` 做硬超时）
  - `chat_completion_stream()` — 流式调用，AsyncIterator[str]
  - `chat_completion_full()` — 非流式调用，返回完整文本
  - `count_tokens()` — token 估算
- **llm_config.py**: 多模型配置管理。在 `LLM_PROVIDERS` 列表中集中配置所有模型服务，重试时按顺序自动切换。支持通过 `extra_body` 传递额外参数（如 `top_k`、`chat_template_kwargs` 等）。

核心特性：
- 多模型备用切换（重试时轮换 provider）
- 超时控制（非流式使用 `asyncio.wait_for` 硬超时，流式首 chunk 10s 超时）
- 异常分类（可重试 vs 不可重试）
- 流式首 chunk 超时重试（已 yield 内容后不重试）
- 调用耗时日志（非流式记录调用耗时，流式记录首 chunk 到达时间和总耗时）

### 3. dal/ — 数据访问层

封装数据库操作，使用 aiosqlite（异步 SQLite）。

- **database.py**: `get_db()` 返回连接，调用方负责关闭。`init_db()` 在启动时建表。
- 其他 DAO 文件按实体拆分，每个文件包含该实体的 CRUD 操作。

调用模式：
```python
async def some_operation():
    db = await get_db()
    try:
        cursor = await db.execute("SQL...", (params,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()
```

### 4. api/ — API 路由层

FastAPI 路由层，负责请求校验、参数提取、调用 service 层、返回响应。

- 每个文件定义一个 `APIRouter`，在 `main.py` 中注册。
- SSE 流式接口使用 `StreamingResponse` + `text/event-stream`。
- 使用 Pydantic `BaseModel` 定义请求体。

SSE 事件格式：
```python
yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
yield f"data: {json.dumps({'type': 'done'})}\n\n"
yield f"data: {json.dumps({'type': 'error', 'content': str(exc)}, ensure_ascii=False)}\n\n"
```

### 5. services/ — 业务逻辑层

按业务模块分目录，每个目录包含该模块的引擎和辅助类。

- **engine.py**: 模块主引擎，协调 LLM 调用、数据库操作、业务逻辑。
- 引擎实例缓存在 api 层的 `_engines: dict` 中，按 `conv_uid` 索引。

### 6. prompts/ — 提示词管理

按模块组织提示词，每个文件包含：
- 系统提示常量（`XXX_SYSTEM`）
- 提示模板（`XXX_TEMPLATE`）
- 构建 messages 的函数（`build_xxx_messages()`）
- 解析 LLM 输出的函数（`parse_xxx_response()`）

## 关键设计模式

### .env 驱动配置
所有可配置项通过环境变量读取，代码中提供合理默认值。配置文件在模块加载时执行目录创建。

### 会话级日志
每个会话（conv_uid）独立日志文件，便于排查问题。日志同时输出到文件和控制台。

### 多模型容错
LLM 调用支持多 provider 配置，重试时自动轮换。流式调用在首个内容 chunk 超时后重试，已开始输出后不再重试。

### SSE 流式响应
所有对话类接口使用 SSE 流式返回，统一事件类型：`text`（内容块）、`done`（完成）、`error`（异常）。

### 文件存储
`storage/` 目录用于存放项目运行时所需的文件（数据库文件、用户上传文件、临时文件、静态资源等）。
脚手架仅创建顶层 `storage/` 目录，**不预生成任何子目录结构**——具体的目录划分由实际业务需求决定，
运行时代码（如 `config.py` 中的 `os.makedirs`）会按需自动创建所需子目录。
例如上传文件可按 `{user}/{module}/{conv_uid}/` 分层存储，删除会话时递归清理对应目录。
