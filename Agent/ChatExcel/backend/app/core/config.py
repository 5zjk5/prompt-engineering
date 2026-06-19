"""Chat Excel 独立项目配置 — 全部由 .env 驱动"""

import os
from dotenv import load_dotenv

# 从 backend/ 目录和项目根目录加载 .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=False)


# ── LLM 配置 ──────────────────────────────────────────────
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ── 服务配置 ──────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "7396"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

# ── 文件上传 ──────────────────────────────────────────────
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'uploads'))
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_EXTENSIONS: set = {".xlsx", ".xls", ".csv", ".json", ".parquet"}

# ── 数据库 ────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'db', 'chat_excel.db'))

# ── 沙箱 ──────────────────────────────────────────────────
SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "60"))
SANDBOX_MAX_MEMORY_MB: int = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))
SANDBOX_MAX_OUTPUT_CHARS: int = int(os.getenv("SANDBOX_MAX_OUTPUT_CHARS", "2000"))

# ── 上下文压缩 ────────────────────────────────────────────
CONTEXT_MAX_TOKENS: int = int(os.getenv("CONTEXT_MAX_TOKENS", "120000"))
CONTEXT_RESERVED_TOKENS: int = int(os.getenv("CONTEXT_RESERVED_TOKENS", "4096"))
CONTEXT_WARNING_THRESHOLD: float = float(os.getenv("CONTEXT_WARNING_THRESHOLD", "0.70"))
CONTEXT_ERROR_THRESHOLD: float = float(os.getenv("CONTEXT_ERROR_THRESHOLD", "0.90"))

# ── ReAct Agent ────────────────────────────────────────────
REACT_MAX_RETRY_COUNT: int = int(os.getenv("REACT_MAX_RETRY_COUNT", "30"))
SHORT_TERM_MEMORY_BUFFER_SIZE: int = int(os.getenv("SHORT_TERM_MEMORY_BUFFER_SIZE", "5"))
SKILLS_DIR: str = os.getenv("SKILLS_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'skills'))

# ── DuckDB ────────────────────────────────────────────────
DUCKDB_DIR: str = os.getenv("DUCKDB_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'duckdb'))

# ── 日志 ──────────────────────────────────────────────────
LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))

# ── 确保目录存在 ─────────────────────────────────────────
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(DUCKDB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)