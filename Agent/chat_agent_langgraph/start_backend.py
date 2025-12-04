import uvicorn
import uuid
import json
import aiosqlite
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from config.config import config, db_path, service_logger, llm_text, llm_img
from config.create_db import create_database


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
                await cursor.execute("SELECT user FROM user_info")
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
                await cursor.execute(
                    "SELECT user FROM user_info WHERE user = ?", (username,)
                )
                existing_user = await cursor.fetchone()

                if existing_user:
                    service_logger.error(f"创建用户失败: 用户名 {username} 已存在")
                    return {"error": "用户名已存在"}

                # 插入新用户
                await cursor.execute(
                    "INSERT INTO user_info (user, user_id) VALUES (?, ?)",
                    (username, user_id),
                )

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
                await cursor.execute(
                    "SELECT user_id FROM user_info WHERE user = ?",
                    (user.user_name,),
                )
                result = await cursor.fetchone()

                # 如果用户不存在，返回错误
                if result is None:
                    service_logger.error(f"用户 {user.user_name} 不存在")
                    return {"error": f"用户 {user.user_name} 不存在"}

                user_id = result[0]

                # 查询该用户的所有会话
                await cursor.execute(
                    "SELECT session_id, title, created_at FROM session_info WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                )
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
                    await cursor.execute(
                        "DELETE FROM session_info WHERE session_id = ?",
                        (request.session_id,),
                    )

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
                    await cursor.execute(
                        "UPDATE session_info SET title = ? WHERE session_id = ?",
                        (request.title, request.session_id),
                    )

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
                await cursor.execute(
                    "SELECT user_id FROM user_info WHERE user = ?",
                    (user.user_name,),
                )
                result = await cursor.fetchone()

                # 如果用户不存在，创建新用户
                if result is None:
                    service_logger.warning(f"用户 {user.user_name} 不存在，创建新用户")
                    user_id = str(uuid.uuid4())
                    await cursor.execute(
                        "INSERT INTO user_info (user, user_id) VALUES (?, ?)",
                        (user.user_name, user_id),
                    )
                else:
                    user_id = result[0]

                # 生成新的session ID
                session_id = str(uuid.uuid4())

                # 插入新的session记录
                await cursor.execute(
                    "INSERT INTO session_info (user_id, session_id) VALUES (?, ?)",
                    (user_id, session_id),
                )

                # 提交更改
                await conn.commit()

                # 记录会话创建日志
                service_logger.info(
                    f"用户 {user.user_name} (ID: {user_id}) 创建新会话 {session_id}"
                )

        # 返回session ID和用户ID
        return {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": user.user_name,
        }

    except Exception as e:
        service_logger.error(f"创建会话失败： {str(e)}")
        return {"error": f"创建会话失败： {str(e)}"}


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
        service_logger.info(f"对话日志：log/chat_log/{user_id}/{session_id}.log")

        # 创建消息列表
        messages = [HumanMessage(content=query)]

        # 定义异步生成器函数，用于流式返回结果
        async def generate():
            try:
                # 调用大模型的流式生成方法
                async for chunk in llm_text.astream(messages):
                    # 提取内容
                    content = chunk.content
                    if content:
                        # 构造JSON格式的响应
                        response = {
                            "content": content,
                            "content_type": chunk.response_metadata.get(
                                "content_type", "content"
                            ),
                            "chunk_index": chunk.response_metadata.get(
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

            except Exception as e:
                service_logger.error(f"流式生成过程中出错: {str(e)}")
                error_response = {
                    "error": f"生成回复时出错: {str(e)}",
                    "content_type": "error",
                }
                yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"

        # 返回流式响应
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
        service_logger.error(f"处理聊天请求时出错: {str(e)}")
        return {"error": f"处理请求时出错: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
