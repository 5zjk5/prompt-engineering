import uvicorn
import uuid
import json
import aiosqlite
import asyncio
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessage, SystemMessage
from config.create_db import create_database
from utils.logger import chat_log
from agent.memery import Memory
from agent.agent import create_agent_graph
from agent.utils import get_messages
from agent.configuration import Configuration
from config.config import (
    config,
    db_path,
    service_logger,
    llm_text,
    llm_img,
    chat_log_path,
    system_chat_prompt,
)


class UserRequest(BaseModel):
    user_name: str = "default"


class ChatRequest(BaseModel):
    user_name: str = "default"
    user_id: str
    session_id: str
    query: str
    files: list = []


class SessionTitleRequest(BaseModel):
    user_name: str = "default"
    session_id: str
    title: str
    mode: str = "update"  # 默认为更新模式，可选值为"update"或"delete"


class SessionMessagesRequest(BaseModel):
    user_name: str
    user_id: str
    session_id: str


app = FastAPI(
    title=config["app"]["title"],
    description=config["app"]["description"],
    version=config["app"]["version"],
    lifespan=create_database(),
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["cors"]["allow_origins"],
    allow_credentials=config["cors"]["allow_credentials"],
    allow_methods=config["cors"]["allow_methods"],
    allow_headers=config["cors"]["allow_headers"],
)

# 初始化 agent
app.state.agent_graph = create_agent_graph()


# 用户选择
@app.get("/user_select")
async def get_users():
    """
    查询数据库中的user_info表，返回所有用户名
    """
    try:
        service_logger.info("查询数据库中的 user_info 表，返回所有用户名")

        # 连接数据库，设置超时时间为30秒
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                # 查询所有用户
                sql = "SELECT user FROM user_info"
                await cursor.execute(sql)
                rows = await cursor.fetchall()
                users = [row[0] for row in rows]
                service_logger.info(
                    f"成功查询到 {len(users)} 个用户，用户列表为: {users}"
                )

                return {"users": users}
    except Exception as e:
        service_logger.error(f"查询用户失败: {str(e)}")
        return {"error": f"查询用户失败: {str(e)}"}


# 创建用户
@app.get("/create_user")
async def create_user(username: str = Query(..., description="用户名")):
    """
    创建新用户，将用户信息保存到user_info表中

    Args:
        username: 用户名

    Returns:
        创建结果信息
    """
    try:
        service_logger.info(f"尝试创建用户： {username}")

        # 生成唯一的user_id
        user_id = str(uuid.uuid4())

        # 连接数据库，设置超时时间为30秒
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                # 检查用户名是否已存在
                sql = "SELECT user FROM user_info WHERE user = ?"
                params = (username,)
                await cursor.execute(sql, params)
                existing_user = await cursor.fetchone()

                if existing_user:
                    service_logger.error(f"创建用户失败: 用户名 {username} 已存在")
                    return {"error": "用户名已存在"}

                # 插入新用户
                sql = "INSERT INTO user_info (user, user_id) VALUES (?, ?)"
                params = (username, user_id)
                await cursor.execute(sql, params)

                # 提交更改
                await conn.commit()

                service_logger.info(f"用户 {username} 成功创建，用户 ID 为: {user_id}")
                return {"message": "用户创建成功", "user": username, "user_id": user_id}

    except Exception as e:
        service_logger.error(f"创建用户失败: {str(e)}")
        return {"error": f"创建用户失败: {str(e)}"}


# 获得用户的所有 session
@app.post("/user_session")
async def get_user_session(user: UserRequest):
    try:
        service_logger.info(f"尝试获取用户会话： {user.user_name}")

        # 连接数据库，设置超时时间为30秒
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                # 根据用户名查询用户ID
                sql = "SELECT user_id FROM user_info WHERE user = ?"
                params = (user.user_name,)
                await cursor.execute(sql, params)
                result = await cursor.fetchone()

                # 如果用户不存在，返回错误
                if result is None:
                    service_logger.error(f"用户 {user.user_name} 不存在")
                    return {"error": f"用户 {user.user_name} 不存在"}

                user_id = result[0]

                # 查询该用户的所有会话
                sql = "SELECT session_id, title, created_at FROM session_info WHERE user_id = ? ORDER BY created_at DESC"
                params = (user_id,)
                await cursor.execute(sql, params)
                sessions = await cursor.fetchall()

                # 格式化会话数据
                session_list = []
                for session in sessions:
                    session_id, title, created_at = session
                    session_list.append(
                        {
                            "session_id": session_id,
                            "title": title,
                            "created_at": created_at,
                        }
                    )

                service_logger.info(
                    f"成功获取用户 {user.user_name} 的 {len(session_list)} 个会话，user_id: {user_id}"
                )
                return {"user_id": user_id, "sessions": session_list}

    except Exception as e:
        service_logger.error(f"获取用户会话失败： {str(e)}")
        return {"error": f"获取用户会话失败： {str(e)}"}


# 更新、删除会话标题
@app.post("/update_session_title")
async def update_session_title(request: SessionTitleRequest):
    try:
        # 根据模式记录不同的日志
        if request.mode == "delete":
            service_logger.info(
                f"用户 {request.user_name} 尝试删除会话： {request.session_id}"
            )
        else:
            service_logger.info(
                f"用户 {request.user_name} 尝试更新会话标题： {request.session_id} -> {request.title}"
            )

        # 连接数据库，设置超时时间为30秒
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                if request.mode == "delete":
                    # 删除会话
                    sql = "DELETE FROM session_info WHERE session_id = ?"
                    params = (request.session_id,)
                    await cursor.execute(sql, params)

                    # 同时删除 history_multi_turn 表中对应 session_id 的记录
                    sql_history = "DELETE FROM history_multi_turn WHERE session_id = ?"
                    await cursor.execute(sql_history, params)

                    # 提交更改
                    await conn.commit()

                    # 检查是否有行被删除
                    if cursor.rowcount == 0:
                        service_logger.error(
                            f"用户 {request.user_name} 尝试删除的会话 {request.session_id} 不存在"
                        )
                        return {"error": f"会话 {request.session_id} 不存在"}

                    service_logger.info(
                        f"用户 {request.user_name} 成功删除会话 {request.session_id}"
                    )
                    return {"success": True, "message": "会话删除成功"}
                else:
                    # 更新会话标题
                    sql = "UPDATE session_info SET title = ? WHERE session_id = ?"
                    params = (request.title, request.session_id)
                    await cursor.execute(sql, params)

                    # 提交更改
                    await conn.commit()

                    # 检查是否有行被更新
                    if cursor.rowcount == 0:
                        service_logger.error(
                            f"用户 {request.user_name} 尝试更新的会话 {request.session_id} 不存在"
                        )
                        return {"error": f"会话 {request.session_id} 不存在"}

                    service_logger.info(
                        f"用户 {request.user_name} 成功更新会话 {request.session_id} 的标题为 {request.title}"
                    )
                    return {"success": True, "message": "会话标题更新成功"}

    except Exception as e:
        service_logger.error(f"操作会话失败： {str(e)}")
        return {"error": f"操作会话失败： {str(e)}"}


# 新建会话
@app.post("/create_session")
async def create_session(user: UserRequest):
    try:
        service_logger.info(f"尝试给用户 {user.user_name} 创建新会话")

        # 连接数据库，设置超时时间为30秒
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                # 根据用户名查询用户ID
                sql = "SELECT user_id FROM user_info WHERE user = ?"
                params = (user.user_name,)
                await cursor.execute(sql, params)
                result = await cursor.fetchone()

                # 如果用户不存在，创建新用户
                if result is None:
                    service_logger.warning(f"用户 {user.user_name} 不存在，创建新用户")
                    user_id = str(uuid.uuid4())
                    sql = "INSERT INTO user_info (user, user_id) VALUES (?, ?)"
                    params = (user.user_name, user_id)
                    await cursor.execute(sql, params)
                else:
                    user_id = result[0]

                # 生成新的session ID
                session_id = str(uuid.uuid4())

                # 插入新的session记录，默认标题为"新建对话"
                sql = "INSERT INTO session_info (user_id, session_id, title) VALUES (?, ?, ?)"
                params = (user_id, session_id, "新建对话")
                await cursor.execute(sql, params)

                # 提交更改
                await conn.commit()

                # 记录会话创建日志
                service_logger.info(
                    f"用户 {user.user_name} (ID: {user_id}) 创建新会话 {session_id}"
                )

        # 返回session ID、用户ID和默认标题
        return {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": user.user_name,
            "title": "新建对话",
        }

    except Exception as e:
        service_logger.error(f"创建会话失败： {str(e)}")
        return {"error": f"创建会话失败： {str(e)}"}


# 获取会话历史消息
@app.post("/session_messages")
async def get_session_messages(request: SessionMessagesRequest):
    """
    获取指定会话的历史消息

    Args:
        request: 包含用户名、用户ID和会话ID的请求体

    Returns:
        包含历史消息的JSON响应
    """
    try:
        user_name = request.user_name
        user_id = request.user_id
        session_id = request.session_id

        service_logger.info(
            f"收到获取历史消息请求: 用户名={user_name}, 用户ID={user_id}, 会话ID={session_id}"
        )

        # 连接数据库
        async with aiosqlite.connect(db_path) as conn:
            async with conn.cursor() as cursor:
                # 查询历史消息，按照turn_id升序排序
                sql = "SELECT * FROM history_multi_turn WHERE session_id = ? AND user_id = ? ORDER BY turn_id ASC"
                params = (session_id, user_id)
                await cursor.execute(sql, params)

                # 获取查询结果
                rows = await cursor.fetchall()

                # 格式化结果
                messages = []
                for row in rows:
                    messages.append(
                        {
                            "session_id": row[0],
                            "user_id": row[1],
                            "turn_id": row[2],
                            "query": row[3],
                            "answer": row[4],
                            "img_content": row[5],
                            "timestamp": row[6],
                        }
                    )

                service_logger.info(
                    f"获取历史消息成功: 会话ID={session_id}, 对话轮次数={len(messages)}"
                )
                return {"success": True, "messages": messages, "session_id": session_id}
    except Exception as e:
        service_logger.error(f"获取历史消息失败: {str(e)}")
        return {
            "success": False,
            "error": f"获取历史消息失败: {str(e)}",
            "session_id": request.session_id,
        }


# 对话接口
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    接收用户ID、会话ID和消息，调用大模型并流式返回结果

    Args:
        request: 包含用户ID、会话ID和消息的请求体

    Returns:
        流式响应，包含大模型的生成结果
    """
    try:
        user = request.user_name
        user_id = request.user_id
        session_id = request.session_id
        query = request.query
        files = request.files

        service_logger.info(
            f"收到聊天请求: 用户={user}, 用户ID={user_id}, 会话ID={session_id}, 文件数={len(files)}, 查询={query}"
        )
        log_path = f"{chat_log_path}/{user}_{user_id}/{session_id}.log"
        service_logger.info(f"对话日志：{log_path}")

        # 创建对话日志
        chat_logger = chat_log(log_path, logfile_level="INFO")

        # 使用chat_logger记录聊天请求信息
        chat_logger.info(f"==========开始处理聊天请求==========")
        chat_logger.info(f"收到聊天请求: 查询={query}, 文件数={len(files)}")

        # 是否有图片选择模型
        llm = llm_text if not files else llm_img

        # 获取历史消息列表
        history_messages = await Memory.get_chat_history(
            user_id, session_id, chat_logger
        )
        messages = [SystemMessage(content=system_chat_prompt)] + history_messages

        # 拼接当前 messages
        current_message = get_messages(query, files)
        messages += current_message

        # 定义异步生成器函数，用于流式返回结果
        async def generate():
            try:
                # 调用大模型的流式生成方法
                agent_graph = app.state.agent_graph
                final_answer = ""
                async for chunk in agent_graph.astream(
                    {"messages": messages},
                    stream_mode="messages",
                    context=Configuration(
                        llm=llm,
                        logger=chat_logger,
                        user_id=user_id,
                        session_id=session_id,
                    ),
                ):
                    # 提取内容
                    content = chunk[0].content
                    final_answer += content
                    if content:
                        # 构造JSON格式的响应
                        response = {
                            "content": content,
                            "content_type": chunk[0].response_metadata.get(
                                "content_type", "content"
                            ),
                            "chunk_index": chunk[0].response_metadata.get(
                                "chunk_index", "0"
                            ),
                        }
                        # 发送JSON格式的数据
                        yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"

                # 发送结束标记
                end_response = {
                    "content": "",
                    "content_type": "end",
                    "chunk_index": "-1",
                }
                yield f"data: {json.dumps(end_response, ensure_ascii=False)}\n\n"

                # 保存历史消息，使用 asyncio.create_task 创建一个异步任务，不等待其完成
                messages.append(AIMessage(content=final_answer))
                asyncio.create_task(
                    Memory.save_chat_history(user_id, session_id, messages, chat_logger)
                )

            except asyncio.CancelledError:
                # 捕获任务取消异常，这通常是客户端断开连接导致的
                chat_logger.info(
                    f"客户端已断开连接，停止流式输出: {user_id}/{session_id}"
                )
                chat_logger.info(
                    f"客户端已断开连接，停止流式输出: {user_id}/{session_id}"
                )
                # 直接返回，停止生成器
                return
            except Exception as e:
                # 检查是否是客户端断开连接导致的其他异常
                if any(
                    keyword in str(e).lower()
                    for keyword in ["disconnect", "abort", "reset", "close"]
                ):
                    chat_logger.info(
                        f"客户端已断开连接，停止流式输出: {user_id}/{session_id}"
                    )
                    # 不需要返回错误信息，直接终止生成器
                    return
                else:
                    import traceback
                    chat_logger.error(traceback.format_exc())
                    chat_logger.error(f"流式生成过程中出错: {str(e)}")
                    error_response = {
                        "error": f"生成回复时出错: {str(e)}",
                        "content_type": "error",
                    }
                    yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
            finally:
                chat_logger.info(f"==========处理聊天请求完成==========")

        # 返回流式响应，添加Response参数以支持取消
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
            },
        )

    except Exception as e:
        import traceback

        service_logger.error(traceback.format_exc())
        service_logger.error(f"处理聊天请求时出错: {str(e)}")
        return {"error": f"处理请求时出错: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
