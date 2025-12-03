import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.config import config
from config.create_db import create_database


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
def read_root():
    return {"message": "Welcome to LangGraph Agent API"}


# 创建用户
@app.get("/create_user")
def get_users():
    return {"message": "create_user"}


# 新建会话
@app.post("/create_session")
def create_user(user):
    return user


# 用户 id
@app.get("/user_id")
def get_conversations():
    return []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
