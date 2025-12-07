import sqlite3
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from config.config import db_path


class Memory:

    @classmethod
    async def get_chat_history(cls, user_id: str, session_id: str, chat_logger):
        """
        获取聊天历史记录

        :param user_id: 用户ID
        :param session_id: 会话ID
        :param chat_logger: 日志记录器
        :return: 聊天历史记录列表
        """
        chat_logger.info(f"获取聊天历史记录...")
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 查询历史记录
            cursor.execute(
                "SELECT query, answer FROM history_multi_turn WHERE session_id = ? AND user_id = ? ORDER BY turn_id",
                (session_id, user_id),
            )
            rows = cursor.fetchall()

            # 格式化历史记录
            history_messages = []
            for query, answer in rows:
                history_messages.append(HumanMessage(content=query))
                history_messages.append(AIMessage(content=answer))

            chat_logger.info(f"获取聊天历史记录成功, 历史轮次数: {len(history_messages) // 2}")
            return history_messages
        except Exception as e:
            chat_logger.error(f"获取聊天历史记录失败: {e}")
            return []
        finally:
            # 关闭数据库连接
            conn.close()

    @classmethod
    async def save_chat_history(cls, user_id: str, session_id: str, messages: List, chat_logger):
        """
        保存聊天历史记录

        :param user_id: 用户ID
        :param session_id: 会话ID
        :param messages: 消息列表
        :param chat_logger: 日志记录器
        """
        chat_logger.info(f">>> 单独线程保存聊天历史记录...")

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 只处理最后一轮的消息，即最后两条消息（一条用户消息和一条AI消息）
            if len(messages) >= 2:
                # 计算当前轮次，messages的长度除以2，得到商，就是当前一轮
                current_turn_id = len(messages) // 2
                chat_logger.info(f">>> 当前轮次: {current_turn_id}")

                # 获取最后两条消息
                user_message = messages[-2]
                ai_message = messages[-1]

                # 检查消息类型
                if user_message.type == "human" and ai_message.type == "ai":
                    # 保存到数据库
                    cursor.execute(
                        "INSERT INTO history_multi_turn (session_id, user_id, turn_id, query, answer) VALUES (?, ?, ?, ?, ?)",
                        (
                            session_id,
                            user_id,
                            current_turn_id,
                            user_message.content,
                            ai_message.content,
                        ),
                    )

                    # 提交事务
                    conn.commit()
                    chat_logger.info(f">>> 保存聊天历史记录成功...")
                else:
                    chat_logger.info(f">>> 消息列表最后两条消息不是用户消息和AI消息，无法保存聊天历史记录...")
            else:
                chat_logger.info(f">>> 消息列表长度不足2，无法保存聊天历史记录...")
        except Exception as e:
            # 回滚事务
            conn.rollback()
            chat_logger.error(f">>> 保存聊天历史记录失败: {str(e)}")
        finally:
            # 关闭连接
            cursor.close()
            conn.close()
