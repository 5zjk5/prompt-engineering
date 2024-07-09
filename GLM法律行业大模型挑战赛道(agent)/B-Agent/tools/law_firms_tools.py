# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from api.data_query_api import *


class QueryConds(BaseModel):
    query_conds: dict = Field(description="""
    需要查询的信息的字典，例如查询公司名称：
    `{"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []}`
    need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    """)


class keyValue(BaseModel):
    key: str = Field(description='键')
    value: str = Field(description='值')


# 根据律师事务所查询律师事务所名录
lawfirm_info = StructuredTool.from_function(
    func=get_lawfirm_info,
    name="get_lawfirm_info",
    args_schema=keyValue,
    description="""
    根据`律师事务所名称`查询律师事务所名录（注册相关信息）。
    注册相关信息包含律师事务所名称，律师事务所唯一编码，律师事务所负责人，事务所注册资本，事务所成立日期，律师事务所地址，通讯电话，通讯邮箱，律所登记机关。
    """
)

# 根据律师事务所查询律师事务所统计数据
lawfirm_log = StructuredTool.from_function(
    func=get_lawfirm_log,
    name="get_lawfirm_log",
    args_schema=keyValue,
    description="""
    根据`律师事务所`查询律师事务所统计数据。
    统计数据包含业务量排名，服务已上市公司数量，报告期间所服务上市公司违规事件数量，报告期所服务上市公司接受立案调查数量。
    """
)

# 关于法院的工具集合
law_firms_tools = [
    lawfirm_info,
    lawfirm_log,
]
