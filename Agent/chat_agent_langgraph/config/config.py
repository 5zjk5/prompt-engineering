import os
import yaml
from pathlib import Path
from utils.ChatOpenAIModel_LangChian import ChatOpenAIModel
from utils.logger import service_log


# 简单的配置加载函数
def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 加载配置
config = load_config()

# 加载大模型
llm_text = ChatOpenAIModel(
    api_key=config["GLM"]["API_KEY"],
    base_url=config["GLM"]["BASE_URL"],
    extra_body={
        "thinking": {
            "type": "disabled",
        },
    },
    model=config["GLM"]["MODEL"],
)
llm_img = ChatOpenAIModel(
    api_key=config["GLM"]["API_KEY"],
    base_url=config["GLM"]["BASE_URL"],
    extra_body={
        "thinking": {
            "type": "disabled",
        },
    },
    model=config["GLM"]["IMG_MODEL"],
)

# 数据库路径
db_path = config["database"]["url"]

# 后端服务操作日志
service_log_path = config["log"]["service_log_path"]
service_logger = service_log(service_log_path=service_log_path, logfile_level="INFO")

# 对话日志存储路径
chat_log_path = config["log"]["chat_log_path"]

# 系统对话提示
system_chat_prompt = config["SYSTEM_CHAT_PROMPT"]

# 嵌入模型
embedding_model_path = config["embedding_model_path"]
