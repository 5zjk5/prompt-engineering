from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# 导入配置模块
from config.config import config

app = FastAPI(
    title=config["app"]["title"],
    description=config["app"]["description"],
    version=config["app"]["version"],
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["cors"]["allow_origins"],
    allow_credentials=config["cors"]["allow_credentials"],
    allow_methods=config["cors"]["allow_methods"],
    allow_headers=config["cors"]["allow_headers"],
)


# 数据模型
class User(BaseModel):
    id: str
    name: str


class Message(BaseModel):
    id: Optional[str] = None
    type: str  # "user" or "ai"
    content: str
    images: List[str] = []
    timestamp: Optional[str] = None


class Conversation(BaseModel):
    id: Optional[str] = None
    title: str
    preview: str
    content: str
    messages: List[Message] = []


# 根路径
@app.get("/")
def read_root():
    return {"message": "Welcome to LangGraph Agent API"}


# 用户相关接口
@app.get("/users", response_model=List[User])
def get_users():
    """获取用户列表"""
    return []


@app.post("/users", response_model=User)
def create_user(user: User):
    """创建新用户"""
    return user


# 对话相关接口
@app.get("/conversations", response_model=List[Conversation])
def get_conversations():
    """获取对话列表"""
    return []


@app.get("/conversations/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str):
    """获取单个对话"""
    raise HTTPException(status_code=404, detail="Conversation not found")


@app.post("/conversations", response_model=Conversation)
def create_conversation(conversation: Conversation):
    """创建新对话"""
    return conversation


@app.put("/conversations/{conversation_id}", response_model=Conversation)
def update_conversation(conversation_id: str, conversation: Conversation):
    """更新对话"""
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """删除对话"""
    return {"message": "Conversation deleted"}


# 消息相关接口
@app.post("/conversations/{conversation_id}/messages", response_model=Message)
def create_message(conversation_id: str, message: Message):
    """发送消息"""
    return message


# 图片上传接口
@app.post("/upload/image")
def upload_image():
    """上传图片"""
    return {"message": "Image uploaded"}
