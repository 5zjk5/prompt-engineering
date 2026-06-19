"""模块1 ChatExcel API 接口 — SSE 流式

支持两种场景:
1. 有文件: DuckDB SQL 分析
2. 无文件: 纯 LLM 对话（用于基础连通测试）
"""

import json
import traceback
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_excel.engine import ChatExcelEngine
from app.llm.client import chat_completion_stream
from app.core.logger import get_session_logger
from app.llm.llm_config import get_default_llm_provider

router = APIRouter()

# 会话级引擎缓存
_engines: dict = {}


class ChatExcelRequest(BaseModel):
    user_input: str = ""
    conv_uid: str = ""
    file_path: str = ""
    file_name: str = ""
    model_name: str = ""


@router.post("/excel")
async def chat_excel(req: ChatExcelRequest):
    """模块1 ChatExcel — SSE 流式接口"""
    conv_uid = req.conv_uid or uuid.uuid4().hex
    logger = get_session_logger(conv_uid, "chat_excel")
    logger.info("===== [CHAT_EXCEL] 收到对话请求 =====")
    logger.info("参数: user_input=%s, conv_uid=%s, file_path=%s, file_name=%s",
                req.user_input[:100] if req.user_input else "", conv_uid, req.file_path, req.file_name)

    if conv_uid not in _engines and req.user_input and req.user_input.strip():
        engine = ChatExcelEngine(conv_uid=conv_uid)
        if engine.reader.table_infos:
            _engines[conv_uid] = engine
            logger.info("从已存在的 DuckDB 数据恢复引擎: conv_uid=%s", conv_uid)

    # 无文件时走纯 LLM 对话（仅当用户实际输入了问题）
    if not req.file_path and conv_uid not in _engines and req.user_input and req.user_input.strip():
        logger.info("【分支1】无文件+无引擎，走纯 LLM 对话")
        async def simple_chat_stream():
            try:
                full_text = ""
                logger.info("纯 LLM 对话调用，user_input=%s", req.user_input[:100])
                default_llm = get_default_llm_provider()
                logger.info(
                    "LLM 调用参数: stage=chat_excel_simple, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d",
                    default_llm.model,
                    0.7,
                    default_llm.max_tokens,
                    True,
                    1,
                )
                async for chunk in chat_completion_stream(
                    messages=[{"role": "user", "content": req.user_input}],
                    temperature=0.7,
                ):
                    full_text += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
                if not full_text:
                    logger.warning("纯 LLM 对话返回空内容")
                    yield f"data: {json.dumps({'type': 'text', 'content': '(无回复)'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                logger.info("纯 LLM 对话完成，共计 %d 字符", len(full_text))
            except Exception as exc:
                logger.error("ChatExcel SSE 异常: error_type=%s error=%s\n%s", type(exc).__name__, exc, traceback.format_exc())
                yield f"data: {json.dumps({'type': 'error', 'content': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(simple_chat_stream(), media_type="text/event-stream")

    # 有文件时走 ChatExcel 引擎
    if conv_uid not in _engines:
        logger.info("【分支2】创建新 ChatExcel 引擎: conv_uid=%s", conv_uid)
        _engines[conv_uid] = ChatExcelEngine(
            conv_uid=conv_uid,
            file_path=req.file_path,
            file_name=req.file_name or "data.xlsx",
        )
    elif req.file_path and not _engines[conv_uid].reader.table_infos:
        logger.info("引擎已存在但无表数据，追加文件: %s", req.file_path)
        _engines[conv_uid].add_file(req.file_path, req.file_name or "data.xlsx")

    engine = _engines[conv_uid]

    async def event_stream():
        try:
            logger.info("开始 ChatExcel 流式分析")
            async for event in engine.chat_stream(req.user_input):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            logger.info("ChatExcel 流式分析结束")
        except Exception as exc:
            logger.error("ChatExcel SSE 异常: error_type=%s error=%s\n%s", type(exc).__name__, exc, traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
