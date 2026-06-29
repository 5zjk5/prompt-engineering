"""文件上传接口 — 按 用户/模式 分层存储

目录结构:
  uploads/
    default/          <- user_no = "default"
      chat_excel/
        xxx_file.xlsx
      react_agent/
        xxx_file.xlsx
    user_123/         <- user_no = "user_123"
      chat_excel/
        ...
      react_agent/
        ...
"""

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core import config
from app.core.logger import get_session_logger

router = APIRouter()


def _resolve_upload_dir(user_no: str, chat_mode: str, conv_uid: str = "") -> str:
    """根据用户、模式和会话计算上传目录，并确保目录存在"""
    # 安全校验：不允许路径穿越
    safe_user = user_no.replace("..", "").replace("/", "").replace("\\", "").strip() or "default"
    safe_mode = chat_mode.replace("..", "").replace("/", "").replace("\\", "").strip()

    # 只允许两种模式
    if safe_mode not in ("chat_excel", "react_agent"):
        safe_mode = "chat_excel"

    safe_conv_uid = conv_uid.replace("..", "").replace("/", "").replace("\\", "").strip()
    path_parts = [config.UPLOAD_DIR, safe_user, safe_mode]
    if safe_conv_uid:
        path_parts.append(safe_conv_uid)
    upload_dir = os.path.join(*path_parts)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    chat_mode: str = Form("chat_excel"),
    user_no: str = Form("default"),
    conv_uid: str = Form(""),
):
    """上传文件；chat_excel 模式下如果传入 conv_uid，则上传后立即触发学习。"""
    logger = get_session_logger(conv_uid or "no_conv", chat_mode)
    logger.info("===== [UPLOAD] 开始上传文件 =====")
    logger.info("参数: filename=%s, chat_mode=%s, user_no=%s, conv_uid=%s",
                file.filename, chat_mode, user_no, conv_uid)

    # 校验扩展名
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        logger.warning("不支持的文件类型: %s", ext)
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅支持 {config.ALLOWED_EXTENSIONS}",
        )

    # 校验大小
    content = await file.read()
    if len(content) > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        logger.warning("文件大小超限: %d bytes", len(content))
        raise HTTPException(
            status_code=400,
            detail=f"文件超过 {config.MAX_UPLOAD_SIZE_MB}MB 限制",
        )
    logger.info("文件校验通过: ext=%s, size=%d bytes", ext, len(content))

    # 按用户+模式+会话确定存储目录
    upload_dir = _resolve_upload_dir(user_no, chat_mode, conv_uid)

    # 保存文件（用 uuid 防冲突）
    file_id = uuid.uuid4().hex[:12]
    safe_name = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    abs_file_path = os.path.normpath(os.path.abspath(file_path))
    logger.info("文件已保存: %s", abs_file_path)
    learn_result = None
    if chat_mode == "chat_excel" and conv_uid:
        logger.info("【分支1】chat_excel 模式，准备加载文件到引擎")
        from app.api.chat_excel import _engines
        from app.dal.conversation import create_conversation, get_conversation, update_conversation
        from app.services.chat_excel.engine import ChatExcelEngine

        try:
            if not await get_conversation(conv_uid):
                logger.info("创建新对话记录: conv_uid=%s", conv_uid)
                await create_conversation(
                    conv_uid=conv_uid,
                    chat_mode="chat_excel",
                    file_path=abs_file_path,
                    file_name=file.filename,
                    title=file.filename or conv_uid,
                )
            await update_conversation(conv_uid, file_path=abs_file_path, file_name=file.filename)
        except Exception as e:
            logger.warning("更新对话记录失败: %s", e)

        if conv_uid in _engines:
            engine = _engines[conv_uid]
            engine.add_file(abs_file_path, file.filename)
            logger.info("引擎已存在，追加文件: %s", abs_file_path)
        else:
            engine = ChatExcelEngine(
                conv_uid=conv_uid,
                file_path=abs_file_path,
                file_name=file.filename,
            )
            _engines[conv_uid] = engine
            logger.info("创建新引擎: conv_uid=%s", conv_uid)
    elif chat_mode == "react_agent" and conv_uid:
        logger.info("【分支2】react_agent 模式，准备加载文件到引擎")
        from app.api.chat_react import _engines
        from app.dal.conversation import create_conversation, get_conversation, update_conversation
        from app.services.react_agent.engine import ReactEngine

        try:
            if not await get_conversation(conv_uid):
                logger.info("创建新对话记录: conv_uid=%s", conv_uid)
                await create_conversation(
                    conv_uid=conv_uid,
                    chat_mode="react_agent",
                    file_path=abs_file_path,
                    file_name=file.filename,
                    title=file.filename or conv_uid,
                )
            await update_conversation(conv_uid, file_path=abs_file_path, file_name=file.filename)
        except Exception as e:
            logger.warning("更新对话记录失败: %s", e)

        if conv_uid in _engines:
            engine = _engines[conv_uid]
            logger.info("引擎已存在，复用: conv_uid=%s", conv_uid)
        else:
            engine = ReactEngine(
                conv_uid=conv_uid,
                file_path=abs_file_path,
                file_name=file.filename,
            )
            _engines[conv_uid] = engine
            logger.info("创建新引擎: conv_uid=%s", conv_uid)

        if abs_file_path not in engine.file_paths:
            engine.file_paths.append(abs_file_path)
            engine.file_names.append(file.filename or "data file")
        if not engine.file_path:
            engine.file_path = abs_file_path
            engine.file_name = file.filename or "data file"
        logger.info("引擎文件列表已更新: %s", engine.file_paths)
    else:
        logger.info("【分支3】仅保存文件，无引擎操作")

    result = {
        "file_id": file_id,
        "file_path": abs_file_path,
        "file_name": file.filename,
        "file_size": len(content),
        "chat_mode": chat_mode,
        "user_no": user_no,
        "conv_uid": conv_uid,
        "file_learning": bool(learn_result),
        "learning_result": learn_result,
    }
    logger.info("===== [UPLOAD] 上传完成，返回: file_id=%s =====", file_id)
    return result
