# pip install -U "langchain[openai]"
# opanai 官方接口

import os
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI


os.environ["OPENAI_API_KEY"] = "..."

# 方法1
model = init_chat_model("openai:gpt-4.1")
response = model.invoke("你是谁啊？")

# 方法2
model = ChatOpenAI(model="gpt-4.1")
response = model.invoke("介绍你自己？")
