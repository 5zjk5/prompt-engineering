# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from api.data_query_api import *


class QueryConds(BaseModel):
    query_conds: dict = Field(description="""需要查询的信息的字典，例如查询公司名称：
    `{"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []}`
    need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    """)


class keyValue(BaseModel):
    key: str = Field(description='键')
    value: str = Field(description='值')


# 根据法院名称查询法院名录相关信息
court_info = StructuredTool.from_function(
    func=get_court_info,
    name="get_court_info",
    args_schema=keyValue,
    description="""
    根据`法院名称`查询法院名录相关信息，相关信息包含法院名称，法院负责人，成立日期，法院地址，法院联系电话，法院官网。
    """
)

# 根据法院名称或者法院代字查询法院代字等相关数据
court_code = StructuredTool.from_function(
    func=get_court_code,
    name="get_court_code",
    args_schema=keyValue,
    description="""
    根据`法院名称`或者`法院代字`查询法院代字等相关数据.
    相关数据包含法院名称，行政级别，法院级别，法院代字，区划代码，级别。
    """
)

# 关于法院的工具集合
court_tools = [
    court_info,
    court_code,
]
