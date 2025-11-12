# pip install -U "langchain[openai]"
# 微软提供的接口

import os
import time
from langchain.chat_models import init_chat_model
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


os.environ["AZURE_OPENAI_API_KEY"] = "..Y"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://llm-east-us2-test.openai.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-5"  #模型名称作为部署名称如 gpt-5

# 消息列表方法1
conversation1 = [
    {"role": "system", "content": "You are a helpful assistant that translates English to French."},
    {"role": "user", "content": "Translate: I love programming."},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user", "content": "Translate: I love building applications."}
]

# 消息列表方法2
conversation2 = [
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
    AIMessage("J'adore la programmation."),
    HumanMessage("Translate: I love building applications.")
]

# 消息列表方法3
conversation3 = "介绍你自己？"

# 调用方法1
model = init_chat_model(
    "azure_openai:gpt-5",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=3 
    # api_key="..."
)
response = model.invoke("你是谁啊？")
print(f'输入 token：{response.usage_metadata["input_tokens"]}')
print(f'输出 token：{response.usage_metadata["output_tokens"]}')
print(f'总 token：{response.usage_metadata["total_tokens"]}')
print(f'响应内容：{response.content}')


# 调用方法2
model = AzureChatOpenAI(
    model="gpt-5",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0.7,
    timeout=30,
    max_retries=3 
)
response = model.invoke("介绍你自己？")
print(f'输入 token：{response.usage_metadata["input_tokens"]}')
print(f'输出 token：{response.usage_metadata["output_tokens"]}')
print(f'总 token：{response.usage_metadata["total_tokens"]}')
print(f'响应内容：{response.content}')


# 流式调用
for chunk in model.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="", flush=True)
    pass


# 批次调用
batch_prompt = [
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]
start = time.time()
responses = model.batch(batch_prompt)
end = time.time()
print(f'批次调用耗时：{end - start}')
start = time.time()
for prompt in batch_prompt:
    response = model.invoke(prompt)
end = time.time()
print(f'串行调用耗时：{end - start}')
