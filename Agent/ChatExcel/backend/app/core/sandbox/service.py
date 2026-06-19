"""沙箱服务层 — FastAPI 路由 + 全局 SandboxService

复刻自 packages/dbgpt-sandbox/src/dbgpt_sandbox/sandbox/user_layer/service.py
精简: 只保留 connect/execute/disconnect 三个核心操作。
"""

import uuid
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.sandbox.base import ExecutionResult, ExecutionStatus, SessionConfig
from app.core.sandbox.local_runtime import LocalRuntime

from app.core import config

router = APIRouter()


class SandboxService:
    """沙箱服务 — 管理沙箱会话的生命周期"""

    def __init__(self):
        self.runtime = LocalRuntime()

    async def connect(self, session_id: str = None, working_dir: str = "") -> dict:
        if not session_id:
            session_id = uuid.uuid4().hex[:12]

        cfg = SessionConfig(
            language="python",
            timeout=config.SANDBOX_TIMEOUT,
            max_memory=config.SANDBOX_MAX_MEMORY_MB * 1024 * 1024,
            working_dir=working_dir,
        )

        try:
            session = await self.runtime.create_session(session_id, cfg)
            return {"status": "ok", "session_id": session.session_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def execute(self, session_id: str, code: str) -> dict:
        session = await self.runtime.get_session(session_id)
        if not session:
            return {"status": "error", "error": f"会话 {session_id} 不存在"}

        result: ExecutionResult = await session.execute(code)
        return result.to_dict()

    async def disconnect(self, session_id: str) -> dict:
        success = await self.runtime.destroy_session(session_id)
        return {"status": "ok" if success else "error"}

    async def get_session(self, session_id: str) -> Optional[object]:
        return await self.runtime.get_session(session_id)


# 全局单例
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    return _sandbox_service


# ── API 请求模型 ──────────────────────────────────────────

class ConnectRequest(BaseModel):
    session_id: str = ""
    working_dir: str = ""


class ExecuteRequest(BaseModel):
    session_id: str
    code: str


class DisconnectRequest(BaseModel):
    session_id: str


# ── API 路由 ──────────────────────────────────────────────

@router.post("/connect")
async def api_connect(req: ConnectRequest):
    svc = get_sandbox_service()
    return await svc.connect(req.session_id or None, req.working_dir)


@router.post("/execute")
async def api_execute(req: ExecuteRequest):
    svc = get_sandbox_service()
    return await svc.execute(req.session_id, req.code)


@router.post("/disconnect")
async def api_disconnect(req: DisconnectRequest):
    svc = get_sandbox_service()
    return await svc.disconnect(req.session_id)


@router.get("/health")
async def sandbox_health():
    return {"status": "ok"}
