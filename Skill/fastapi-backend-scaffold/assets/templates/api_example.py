"""SSE 流式对话 API 示例 — 演示标准的流式接口写法

复制此文件到 app/api/ 下并重命名，按需修改业务逻辑。
"""

import json
import traceback
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm.client import chat_completion_stream
from app.core.logger import get_session_logger

router = APIRouter()

# 会话级引擎缓存（按需使用）
_engines: dict = {}


class ChatRequest(BaseModel):
    """对话请求体"""
    user_input: str = ""
    conv_uid: str = ""
    model_name: str = ""


@router.post("/chat")
async def chat(req: ChatRequest):
    """SSE 流式对话接口示例"""
    conv_uid = req.conv_uid or uuid.uuid4().hex
    logger = get_session_logger(conv_uid, "chat")
    logger.info("===== [CHAT] 收到对话请求 =====")
    logger.info("参数: user_input=%s, conv_uid=%s", req.user_input[:100] if req.user_input else "", conv_uid)

    async def event_stream():
        """SSE 事件流生成器"""
        try:
            full_text = ""
            async for chunk in chat_completion_stream(
                messages=[{"role": "user", "content": req.user_input}],
            ):
                full_text += chunk
                yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"

            if not full_text:
                yield f"data: {json.dumps({'type': 'text', 'content': '(无回复)'}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info("对话完成，共计 %d 字符", len(full_text))
        except Exception as exc:
            logger.error("SSE 异常: error_type=%s error=%s\n%s", type(exc).__name__, exc, traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
