import sqlite3
import json
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from config.config import db_path, llm_img


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
                "SELECT query, answer, img_content FROM history_multi_turn WHERE session_id = ? AND user_id = ? ORDER BY turn_id",
                (session_id, user_id),
            )
            rows = cursor.fetchall()

            # 格式化历史记录
            history_messages = []
            for query, answer, img_content in rows:
                if img_content:
                    query += f"\n用户上传的图片：\n{img_content}"
                history_messages.append(HumanMessage(content=query))
                history_messages.append(AIMessage(content=answer))

            chat_logger.info(
                f"获取聊天历史记录成功, 历史轮次数: {len(history_messages) // 2}"
            )
            return history_messages
        except Exception as e:
            chat_logger.error(f"获取聊天历史记录失败: {e}")
            return []
        finally:
            # 关闭数据库连接
            conn.close()

    @staticmethod
    def _process_image_content(user_message_content, chat_logger):
        """
        处理包含图片的用户消息，提取文本和识别图片内容
        """
        query = user_message_content
        img_content = None

        # 处理多模态消息（图片）
        if isinstance(user_message_content, list):
            # 提取文本内容
            text_content = ""
            img_messages = []

            for item in user_message_content:
                if item.get("type") == "text":
                    text_content += item.get("text", "")
                elif item.get("type") == "image_url":
                    # 构建图片识别的请求消息
                    img_messages.append(
                        [
                            HumanMessage(
                                content=[
                                    {
                                        "type": "text",
                                        "text": "请详细描述这张图片的内容。请包含以下方面：\n1. 视觉细节：描述场景、人物、物体的位置、颜色和特征。\n2. 文字信息：提取图中出现的所有可见文字。\n3. 时间背景：如果可能，推测图片的时间（如季节、时间段）。\n4. 核心内容：概括图片传达的主要信息或事件。\n请尽可能客观、详尽地描述。",
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": item.get("image_url"),
                                    },
                                ]
                            )
                        ]
                    )

            query = text_content

            # 如果有图片，批量调用模型识别
            if img_messages:
                try:
                    chat_logger.info(f">>> 正在识别 {len(img_messages)} 张图片内容...")
                    # 使用batch接口批量处理
                    batch_responses = llm_img.batch(img_messages)
                    # 提取识别结果
                    img_contents = [resp.content for resp in batch_responses]

                    # 格式化图片内容
                    formatted_parts = []

                    for i, content in enumerate(img_contents):
                        formatted_parts.append(
                            f"第{i + 1}张图片：\n{content.replace('\n', '')}"
                        )

                    img_content = "\n".join(formatted_parts)
                    chat_logger.info(f">>> 图片识别完成")
                except Exception as e:
                    chat_logger.error(f">>> 图片识别失败: {str(e)}")

        return query, img_content

    @classmethod
    async def save_chat_history(
        cls, user_id: str, session_id: str, messages: List, chat_logger
    ):
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
                    # 调用封装的函数处理图片和文本
                    query, img_content = cls._process_image_content(
                        user_message.content, chat_logger
                    )

                    # 保存到数据库
                    cursor.execute(
                        "INSERT INTO history_multi_turn (session_id, user_id, turn_id, query, answer, img_content) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            session_id,
                            user_id,
                            current_turn_id,
                            query,
                            ai_message.content,
                            img_content,
                        ),
                    )

                    # 提交事务
                    conn.commit()
                    chat_logger.info(f">>> 保存聊天历史记录成功...")
                else:
                    chat_logger.info(
                        f">>> 消息列表最后两条消息不是用户消息和AI消息，无法保存聊天历史记录..."
                    )
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
