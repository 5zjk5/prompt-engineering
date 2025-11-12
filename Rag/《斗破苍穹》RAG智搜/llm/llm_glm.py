# coding:utf8
from langchain_openai import ChatOpenAI
from llm.llm_api_key import ZHIPUAI_API_KEY


def zhipu_glm_4(temperature=0.1):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_air(temperature=0.1):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-air",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_flash(temperature=0.9):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-flash",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_long(temperature=0.9):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-long",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_plus(temperature=0.9):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-plus",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_0520(temperature=0.9):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-0520",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def zhipu_glm_4_airx(temperature=0.1):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-airx",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model
