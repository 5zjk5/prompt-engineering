# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_community.tools.tavily_search import TavilyAnswer
import os
from dotenv import load_dotenv


# Tavily 搜索工具 api 在此加载，https://app.tavily.com/home
load_dotenv(r'D:\Python_project\NLP\大模型学习\prompt-engineering\key.env')


class Cat(BaseModel):
    cat: str = Field(description="""猫咪品种名称获得介绍信息，例如美短，金渐层，狸花""")


def cat_info(cat):
    cat = cat.split('\n')[0]
    cats = {
        '美短': '身体健壮',
        '金渐层': '金色的',
        '狸花': '打架最厉害'
    }
    return cats.get(cat)


cat_info_tool = StructuredTool.from_function(
    func=cat_info,
    name="cat_info",
    args_schema=Cat,
    description="""通过猫咪品种名称获得介绍信息，例如美短，金渐层，狸花"""
)


tavily = TavilyAnswer(max_results=1, name="Intermediate Answer")


test_tools = [
    tavily,
    cat_info_tool
]
