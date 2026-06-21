"""FastAPI 后端入口 — 注册路由、中间件、静态文件、启动事件"""

import logging
import os
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import HOST, PORT, DEBUG

app = FastAPI(title="FastAPI Backend", version="1.0.0", debug=DEBUG)
logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_unhandled_exceptions(request: Request, call_next):
    """记录所有普通 HTTP 接口未捕获异常的完整 traceback。"""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(
            "HTTP 接口异常: method=%s path=%s error_type=%s error=%s\n%s",
            request.method,
            request.url.path,
            type(exc).__name__,
            exc,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务端异常", "error_type": type(exc).__name__, "error": str(exc)},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ─────────────────────────────────────────────
# 按需导入并注册路由模块
# from app.api.example import router as example_router
# app.include_router(example_router, prefix="/api", tags=["Example"])

# ── 静态文件服务 ─────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'storage', 'static', 'images')
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=STATIC_DIR), name="images")


@app.on_event("startup")
async def startup():
    """应用启动时初始化数据库"""
    from app.dal.database import init_db
    await init_db()


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    # 注意：reload=True（WatchFiles）在 Windows 下不稳定，
    # 建议生产环境或需要稳定运行时设置 DEBUG=false。
    # 代码变更后手动重启即可。
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
