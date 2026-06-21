"""FastAPI 后端配置 — 全部由 .env 驱动"""

import os
from dotenv import load_dotenv

# 从 backend/ 目录和项目根目录加载 .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=False)


# ── 服务配置 ──────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

# ── 文件上传 ──────────────────────────────────────────────
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'uploads'))
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_EXTENSIONS: set = {".xlsx", ".xls", ".csv", ".json", ".parquet"}

# ── 数据库 ────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'db', 'app.db'))

# ── 上下文压缩（可选，用于 Agent 场景） ────────────────────
CONTEXT_MAX_TOKENS: int = int(os.getenv("CONTEXT_MAX_TOKENS", "120000"))
CONTEXT_RESERVED_TOKENS: int = int(os.getenv("CONTEXT_RESERVED_TOKENS", "4096"))
CONTEXT_WARNING_THRESHOLD: float = float(os.getenv("CONTEXT_WARNING_THRESHOLD", "0.70"))
CONTEXT_ERROR_THRESHOLD: float = float(os.getenv("CONTEXT_ERROR_THRESHOLD", "0.90"))

# ── 日志 ──────────────────────────────────────────────────
LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))

# ── 确保目录存在 ─────────────────────────────────────────
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
