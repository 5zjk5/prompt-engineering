# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from api.data_query_api import *


class QueryConds(BaseModel):
    query_conds: dict = Field(description="""输入格式：{"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []}""")


class keyValue(BaseModel):
    key: str = Field(description='键')
    value: str = Field(description='值')


# 根据`地址`查该地址对应的省份城市区县
address_info = StructuredTool.from_function(
    func=get_address_info,
    name="get_address_info",
    args_schema=keyValue,
    description="""
    根据`地址`查该地址对应的省份城市区县，出现任何关于地址的信息时使用此工具。
    """
)

# 根据省市区查询区划代码
address_code = StructuredTool.from_function(
    func=get_address_code,
    name="get_address_code",
    args_schema=QueryConds,
    description="""
    根据`省份`、`城市`、`区县`查询区划代码，三个字段同时出现才可以使用此工具。
    查询得到信息包含省份，城市，城市区划代码，区县，区县区划代码。
    """
)

# 根据日期及省份城市查询天气相关信息
temp_info = StructuredTool.from_function(
    func=get_temp_info,
    name="get_temp_info",
    args_schema=QueryConds,
    description="""
    根据`日期`及`省份`，`城市`查询天气相关信息，格式：{"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}。
    相关信息包含日期，省份，城市，天气，最高温度，最低温度，湿度。
    """
)

# 关于地址天气的工具集合
address_and_weather_tools = [
    address_info,
    address_code,
    temp_info,
]
