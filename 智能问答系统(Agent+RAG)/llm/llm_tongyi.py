# coding:utf8
from llm.llm_api_key import DASHSCOPE_API_KEY
from langchain_community.llms import Tongyi


def tongyi_qwen_turbo(temperature=1):
    # 通义 qwen-turbo
    model = Tongyi(temperature=temperature, model_name='qwen-turbo', dashscope_api_key=DASHSCOPE_API_KEY)
    return model
