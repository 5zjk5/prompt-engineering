"""对话 CRUD 操作"""

import json
from typing import List, Optional
from app.dal.database import get_db


def _parse_saved_list(value: str) -> List[str]:
    """解析数据库中保存的单个路径或 JSON 数组，统一返回字符串列表"""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
        if isinstance(parsed, str) and parsed:
            return [parsed]
    except Exception:
        pass
    return [value]


def _append_unique_values(existing: str, new_value: str) -> List[str]:
    """把新值追加到已有列表中，并保持顺序去重"""
    values = _parse_saved_list(existing)
    if new_value and new_value not in values:
        values.append(new_value)
    return values


def _format_conversation(row) -> dict:
    """格式化对话记录，兼容旧单文件字段并补充多文件列表字段"""
    conv = dict(row)
    file_paths = _parse_saved_list(conv.get("file_path", ""))
    file_names = _parse_saved_list(conv.get("file_name", ""))
    conv["file_paths"] = file_paths
    conv["file_names"] = file_names
    conv["file_path"] = file_paths[0] if file_paths else ""
    conv["file_name"] = file_names[0] if file_names else ""
    conv["message_count"] = int(conv.get("message_count") or 0)
    return conv


async def create_conversation(
    conv_uid: str,
    chat_mode: str = "chat_excel",
    model_name: str = "",
    file_path: str = "",
    file_name: str = "",
    title: str = "",
) -> dict:
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO conversations (conv_uid, chat_mode, model_name, file_path, file_name, title)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conv_uid, chat_mode, model_name, file_path, file_name, title),
        )
        await db.commit()
        return {"conv_uid": conv_uid, "chat_mode": chat_mode}
    finally:
        await db.close()


async def list_conversations(limit: int = 50, offset: int = 0) -> List[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT c.*, COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conv_uid = c.conv_uid
            GROUP BY c.conv_uid
            ORDER BY c.updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [_format_conversation(row) for row in rows]
    finally:
        await db.close()


async def get_conversation(conv_uid: str) -> Optional[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM conversations WHERE conv_uid = ?", (conv_uid,))
        row = await cursor.fetchone()
        if not row:
            return None
        conv = _format_conversation(row)

        # 获取消息
        cursor = await db.execute(
            "SELECT * FROM messages WHERE conv_uid = ? ORDER BY order_no ASC",
            (conv_uid,),
        )
        messages = [dict(r) for r in await cursor.fetchall()]
        conv["messages"] = messages
        return conv
    finally:
        await db.close()


async def update_conversation(
    conv_uid: str,
    title: str = "",
    chat_mode: str = "",
    file_path: str = "",
    file_name: str = "",
) -> dict:
    db = await get_db()
    try:
        sets = []
        params = []
        if title:
            sets.append("title = ?")
            params.append(title)
        if chat_mode:
            sets.append("chat_mode = ?")
            params.append(chat_mode)
        if file_path or file_name:
            cursor = await db.execute("SELECT file_path, file_name FROM conversations WHERE conv_uid = ?", (conv_uid,))
            row = await cursor.fetchone()
            old_file_path = row["file_path"] if row else ""
            old_file_name = row["file_name"] if row else ""
            if file_path:
                file_paths = _append_unique_values(old_file_path, file_path)
                sets.append("file_path = ?")
                params.append(json.dumps(file_paths, ensure_ascii=False) if len(file_paths) > 1 else file_paths[0])
            if file_name:
                file_names = _append_unique_values(old_file_name, file_name)
                sets.append("file_name = ?")
                params.append(json.dumps(file_names, ensure_ascii=False) if len(file_names) > 1 else file_names[0])
        if sets:
            sets.append("updated_at = CURRENT_TIMESTAMP")
            params.append(conv_uid)
            await db.execute(
                f"UPDATE conversations SET {', '.join(sets)} WHERE conv_uid = ?",
                params,
            )
            await db.commit()
        return {"conv_uid": conv_uid}
    finally:
        await db.close()


async def delete_conversation(conv_uid: str) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM messages WHERE conv_uid = ?", (conv_uid,))
        await db.execute("DELETE FROM conversations WHERE conv_uid = ?", (conv_uid,))
        await db.commit()
        return True
    finally:
        await db.close()


async def add_message(
    conv_uid: str,
    role: str,
    content: str,
    order_no: int = 0,
    metadata: str = "",
) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO messages (conv_uid, role, content, order_no, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (conv_uid, role, content, order_no, metadata),
        )
        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conv_uid = ?",
            (conv_uid,),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_messages(conv_uid: str) -> List[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM messages WHERE conv_uid = ? ORDER BY order_no ASC",
            (conv_uid,),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()
