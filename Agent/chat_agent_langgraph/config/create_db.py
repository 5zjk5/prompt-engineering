import os
import sqlite3
import uuid
from config.config import db_path, service_logger


def create_table_if_not_exists(cursor, table_name, create_sql, table_description):
    """
    检查表是否存在，不存在则创建
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    table_exists = cursor.fetchone()

    if not table_exists:
        service_logger.info(f"{table_description}表不存在，正在创建...")
        cursor.execute(create_sql)
        service_logger.info(f"已创建{table_description}表")
        return True
    return False


def insert_default_user(cursor):
    """
    插入默认用户
    """
    try:
        default_user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO user_info (user, user_id) VALUES (?, ?)",
            ("default", default_user_id),
        )
        service_logger.info(f"已插入默认用户: default (ID: {default_user_id})")
    except sqlite3.Error as e:
        service_logger.error(f"插入默认用户失败: {str(e)}")
        raise


def create_database():
    """
    检查数据库是否存在，不存在则创建，同时创建user_info表和session_info表
    如果数据库存在，检查是否能连通，连通则打印提示，连接失败抛出异常
    """
    # 确保数据库目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        service_logger.info(f"已创建数据库目录: {db_dir}")

    # 检查数据库文件是否存在
    db_exists = os.path.exists(db_path)

    conn = None
    try:
        # 尝试连接数据库，设置超时时间为30秒
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()

        if not db_exists:
            service_logger.info(f"数据库不存在，已创建新数据库: {db_path}")

        # 定义表创建SQL
        user_info_sql = """
            CREATE TABLE user_info (
                user TEXT NOT NULL,
                user_id TEXT PRIMARY KEY
            )
        """

        session_info_sql = """
            CREATE TABLE session_info (
                user_id TEXT,
                session_id TEXT PRIMARY KEY,
                title TEXT DEFAULT '新建对话',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_info(user_id)
            )
        """

        # 创建history_multi_turn表的SQL
        history_multi_turn_sql = """
            CREATE TABLE history_multi_turn (
                session_id TEXT,
                user_id TEXT,
                turn_id INTEGER,
                query TEXT,
                answer TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """

        # 创建或检查user_info表
        user_table_created = create_table_if_not_exists(
            cursor, "user_info", user_info_sql, "user_info"
        )

        # 如果是新数据库或user_info表刚创建，插入默认用户
        if not db_exists or user_table_created:
            insert_default_user(cursor)

        # 创建或检查session_info表
        create_table_if_not_exists(
            cursor, "session_info", session_info_sql, "session_info"
        )

        # 创建或检查history_multi_turn表
        create_table_if_not_exists(
            cursor, "history_multi_turn", history_multi_turn_sql, "history_multi_turn"
        )

        # 提交更改
        conn.commit()

        if not db_exists:
            service_logger.info(f"数据库创建完成: {db_path}")
        else:
            service_logger.info(f"数据库连接成功: {db_path}")

    except sqlite3.Error as e:
        error_msg = f"数据库连接失败: {str(e)}"
        service_logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        # 确保连接总是被关闭
        if conn:
            conn.close()
