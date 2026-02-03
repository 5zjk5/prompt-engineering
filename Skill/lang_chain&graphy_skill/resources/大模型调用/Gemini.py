# pip install -U "langchain[google-genai]"
# 谷歌的模型

import os
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


os.environ["GOOGLE_API_KEY"] = ".."

# 调用方法 必须有 url，且指定为 opanai 才能通，不能指定思考参数 thinking_budget
model = init_chat_model(
    "gemini-2.5-flash",
    model_provider="openai",
    base_url='https://agent.smartedu.lenovo.com/v1beta/openai/',
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=3,
    api_key="..",
)
response = model.invoke("输出数字 12345，不需要其他内容")
print(f'输入 token：{response.usage_metadata["input_tokens"]}')
print(f'输出 token：{response.usage_metadata["output_tokens"]}')
print(f'总 token：{response.usage_metadata["total_tokens"]}')
print(f'响应内容：{response.content}')
