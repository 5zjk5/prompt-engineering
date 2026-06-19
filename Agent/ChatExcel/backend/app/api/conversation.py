"""对话管理 API 接口"""

import gc
import glob
import logging
import os
import shutil

from fastapi import APIRouter
from pydantic import BaseModel

from app.dal.conversation import (
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
    add_message,
    get_messages,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_relative_to(path: str, base_dir: str) -> bool:
    """判断目标路径是否位于指定基础目录内，避免误删外部文件。"""
    try:
        path = os.path.abspath(path)
        base_dir = os.path.abspath(base_dir)
        return os.path.commonpath([path, base_dir]) == base_dir
    except Exception:
        return False


def _collect_conversation_upload_dirs(conv_uid: str, upload_file_paths: set, chat_mode: str) -> set:
    """收集当前会话对应的上传目录，兼容用户/模式/会话分层和历史文件路径。"""
    from app.core import config

    upload_dirs = set()
    upload_root = os.path.abspath(config.UPLOAD_DIR)

    for file_path in upload_file_paths:
        abs_file_path = os.path.abspath(file_path)
        if not _is_relative_to(abs_file_path, upload_root):
            logger.warning(f"跳过非上传目录文件，避免误删: {file_path}")
            continue
        parent_dir = os.path.dirname(abs_file_path)
        if os.path.basename(parent_dir) == conv_uid:
            upload_dirs.add(parent_dir)

    if os.path.exists(upload_root):
        for user_no in os.listdir(upload_root):
            conv_upload_dir = os.path.join(upload_root, user_no, chat_mode, conv_uid)
            if os.path.isdir(conv_upload_dir):
                upload_dirs.add(conv_upload_dir)

    return upload_dirs


class CreateConversationRequest(BaseModel):
    conv_uid: str
    chat_mode: str = "chat_excel"
    model_name: str = ""
    file_path: str = ""
    file_name: str = ""
    title: str = ""


class UpdateConversationRequest(BaseModel):
    title: str = ""
    chat_mode: str = ""
    file_path: str = ""
    file_name: str = ""


class AddMessageRequest(BaseModel):
    conv_uid: str
    role: str
    content: str
    order_no: int = 0
    metadata: str = ""


@router.get("/conversations")
async def api_list_conversations(limit: int = 50, offset: int = 0):
    return await list_conversations(limit, offset)


@router.post("/conversations")
async def api_create_conversation(req: CreateConversationRequest):
    return await create_conversation(
        conv_uid=req.conv_uid,
        chat_mode=req.chat_mode,
        model_name=req.model_name,
        file_path=req.file_path,
        file_name=req.file_name,
        title=req.title,
    )


@router.get("/conversations/{conv_uid}")
async def api_get_conversation(conv_uid: str):
    conv = await get_conversation(conv_uid)
    if not conv:
        return {"error": "Conversation not found"}
    return conv


@router.patch("/conversations/{conv_uid}")
async def api_update_conversation(conv_uid: str, req: UpdateConversationRequest):
    from app.dal.conversation import update_conversation
    return await update_conversation(
        conv_uid,
        title=req.title,
        chat_mode=req.chat_mode,
        file_path=req.file_path,
        file_name=req.file_name,
    )


@router.delete("/conversations/{conv_uid}")
async def api_delete_conversation(conv_uid: str):
    # 先获取对话信息（删除前）
    conv = await get_conversation(conv_uid)
    upload_file_paths = set(conv.get('file_paths', []) if conv else [])
    if conv and conv.get('file_path'):
        upload_file_paths.add(conv['file_path'])

    # 1. 清理引擎缓存 & 关闭 DuckDB 连接
    from app.api.chat_excel import _engines as excel_engines
    from app.api.chat_react import _engines as react_engines
    from app.services.chat_excel.reader import ExcelReader

    if conv_uid in excel_engines:
        try:
            for table_info in excel_engines[conv_uid].reader.table_infos:
                if table_info.get('file_path'):
                    upload_file_paths.add(table_info['file_path'])
            excel_engines[conv_uid].reader.close()
        except Exception as e:
            logger.warning(f"关闭 ExcelReader 失败: {e}")
        del excel_engines[conv_uid]
    # 清理 ExcelReader 类级缓存
    if conv_uid in ExcelReader._instances:
        try:
            for table_info in ExcelReader._instances[conv_uid].table_infos:
                if table_info.get('file_path'):
                    upload_file_paths.add(table_info['file_path'])
            ExcelReader._instances[conv_uid].close()
        except Exception as e:
            logger.warning(f"清理 ExcelReader._instances 失败: {e}")
        del ExcelReader._instances[conv_uid]

    if conv_uid in react_engines:
        try:
            react_engines[conv_uid].close()
        except Exception as e:
            logger.warning(f"关闭 ReactEngine 失败: {e}")
        del react_engines[conv_uid]

    # 强制 GC 释放 DuckDB 文件锁（Windows 必须）
    gc.collect()

    # 2. 清理 DuckDB 文件
    from app.core import config
    duckdb_pattern = os.path.join(config.DUCKDB_DIR, f"_chat_excel_{conv_uid}.duckdb*")
    for f in glob.glob(duckdb_pattern):
        try:
            os.remove(f)
            logger.info(f"已删除 DuckDB 文件: {f}")
        except Exception as e:
            logger.error(f"删除 DuckDB 文件失败 {f}: {e}")

    # 3. 清理当前会话上传目录，兼容历史散落文件
    chat_mode = conv.get('chat_mode', 'chat_excel') if conv else 'chat_excel'
    upload_dirs = _collect_conversation_upload_dirs(conv_uid, upload_file_paths, chat_mode)
    upload_root = os.path.abspath(config.UPLOAD_DIR)

    for file_path in upload_file_paths:
        try:
            abs_file_path = os.path.abspath(file_path)
            if not _is_relative_to(abs_file_path, upload_root):
                continue
            if any(_is_relative_to(abs_file_path, upload_dir) for upload_dir in upload_dirs):
                continue
            if os.path.exists(abs_file_path):
                os.remove(abs_file_path)
                logger.info(f"已删除历史上传文件: {abs_file_path}")
            else:
                logger.warning(f"上传文件不存在: {abs_file_path}")
        except Exception as e:
            logger.error(f"删除历史上传文件失败 {file_path}: {e}")

    for upload_dir in upload_dirs:
        if not _is_relative_to(upload_dir, upload_root) or not os.path.isdir(upload_dir):
            continue
        try:
            shutil.rmtree(upload_dir)
            logger.info(f"已删除会话上传目录: {upload_dir}")
        except Exception as e:
            logger.error(f"删除会话上传目录失败 {upload_dir}: {e}")

    # 4. 清理 SQLite 数据
    success = await delete_conversation(conv_uid)
    if success:
        logger.info(f"已删除会话 {conv_uid} 的 SQLite 数据")
    else:
        logger.warning(f"删除会话 {conv_uid} 的 SQLite 数据失败")

    return {"success": success}


@router.post("/messages")
async def api_add_message(req: AddMessageRequest):
    msg_id = await add_message(
        conv_uid=req.conv_uid,
        role=req.role,
        content=req.content,
        order_no=req.order_no,
        metadata=req.metadata,
    )
    return {"id": msg_id}


@router.get("/messages/{conv_uid}")
async def api_get_messages(conv_uid: str):
    return await get_messages(conv_uid)
