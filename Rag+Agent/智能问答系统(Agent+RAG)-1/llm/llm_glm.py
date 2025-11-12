# coding:utf8
from langchain_openai import ChatOpenAI
from zhipuai import ZhipuAI
from llm.llm_api_key import ZHIPUAI_API_KEY


def zhipu_glm_4(model_name, temperature=0.1):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model=model_name,
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
                       max_tokens=4096
                       )
    return model
