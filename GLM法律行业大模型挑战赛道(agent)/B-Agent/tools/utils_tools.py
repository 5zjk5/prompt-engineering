# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from api.data_query_api import *

class QueryConds(BaseModel):
    nums: list = Field(description="""传入的int、float、str数组，例如：[1, 2, 3, 4, 5]""")


# 求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿，如"1万"
get_sum_toos = StructuredTool.from_function(
    func=get_sum,
    name="get_sum",
    args_schema=QueryConds,
    description="""
    求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿，如"1万"，输入格式：
    [1, 2, 3, 4, 5]
    """
)

# 关于公用工具集合
utils_tools = [
    get_sum_toos,
]
