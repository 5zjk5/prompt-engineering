import os
import sqlite3
from config.config import db_path, service_logger


def create_database():
    """
    检查数据库是否存在，不存在则创建，同时创建user_info表
    如果数据库存在，检查是否能连通，连通则打印提示，连接失败抛出异常
    """
    # 确保数据库目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        service_logger.info(f"已创建数据库目录: {db_dir}")
    
    # 检查数据库文件是否存在
    db_exists = os.path.exists(db_path)
    
    try:
        # 尝试连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if not db_exists:
            service_logger.info(f"数据库不存在，已创建新数据库: {db_path}")
            
            # 创建user_info表
            cursor.execute("""
                CREATE TABLE user_info (
                    user TEXT NOT NULL,
                    user_id TEXT PRIMARY KEY
                )
            """)
            service_logger.info("已创建user_info表")
            
            # 提交更改
            conn.commit()
        else:
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                service_logger.info("user_info表不存在，正在创建...")
                cursor.execute("""
                    CREATE TABLE user_info (
                        user TEXT NOT NULL,
                        user_id TEXT PRIMARY KEY
                    )
                """)
                service_logger.info("已创建user_info表")
                conn.commit()
            
            service_logger.info(f"数据库连接成功: {db_path}")
        
        # 关闭连接
        conn.close()
        
    except sqlite3.Error as e:
        error_msg = f"数据库连接失败: {str(e)}"
        service_logger.error(error_msg)
        raise Exception(error_msg)
