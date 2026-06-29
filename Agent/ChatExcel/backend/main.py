"""Chat Excel 独立项目 — FastAPI 入口"""

import logging
import os
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import HOST, PORT, DEBUG

app = FastAPI(title="Chat Excel", version="1.0.0", debug=DEBUG)
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
from app.api.upload import router as upload_router
from app.api.chat_excel import router as chat_excel_router
from app.api.chat_react import router as chat_react_router
from app.api.conversation import router as conversation_router
from app.api.excel_preview import router as excel_preview_router
from app.api.llm import router as llm_router
from app.core.sandbox.service import router as sandbox_router

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(chat_excel_router, prefix="/api/chat", tags=["ChatExcel"])
app.include_router(chat_react_router, prefix="/api/chat", tags=["ReActAgent"])
app.include_router(conversation_router, prefix="/api", tags=["Conversation"])
app.include_router(excel_preview_router, prefix="/api", tags=["ExcelPreview"])
app.include_router(llm_router, prefix="/api", tags=["LLM"])
app.include_router(sandbox_router, prefix="/api/sandbox", tags=["Sandbox"])

# ── 静态图片服务 ─────────────────────────────────────────
STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), 'storage', 'static', 'images')
os.makedirs(STATIC_IMG_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=STATIC_IMG_DIR), name="images")


@app.on_event("startup")
async def startup():
    from app.dal.database import init_db
    await init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # 注意：reload=True（WatchFiles）在 Windows 下不稳定，
    # 建议生产环境或需要稳定运行时设置 DEBUG=false。
    # 代码变更后手动重启即可。
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)