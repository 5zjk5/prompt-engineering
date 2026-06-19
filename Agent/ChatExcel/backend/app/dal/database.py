"""SQLite 数据库连接与表初始化"""

import aiosqlite
import os

from app.core import config

DB_PATH = config.DB_PATH


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """初始化数据库表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                conv_uid TEXT PRIMARY KEY,
                chat_mode TEXT NOT NULL DEFAULT 'chat_excel',
                model_name TEXT DEFAULT '',
                file_path TEXT DEFAULT '',
                file_name TEXT DEFAULT '',
                title TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_uid TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT DEFAULT '',
                order_no INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conv_uid) REFERENCES conversations(conv_uid)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv_uid ON messages(conv_uid);
        """)
        await db.commit()

        # 兼容已有数据库：添加 metadata 列
        try:
            await db.execute("ALTER TABLE messages ADD COLUMN metadata TEXT DEFAULT ''")
            await db.commit()
        except Exception:
            pass  # 列已存在
