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


# 根据案号查询裁判文书相关信息
legal_document_info_getter = StructuredTool.from_function(
    func=get_legal_document,
    name="get_legal_document",
    args_schema=keyValue,
    description="""
    根据`案号`查询裁判文书相关信息。
    其中案号一般是形如："(2019)沪0115民初61975号".
    相关信息包含关联公司，标题，案号，文书类型，原告，被告，原告律师事务所，被告律师事务所，案由，涉案金额，判决结果，日期，文件名。
    """
)

# 根据`关联公司`查询所有裁判文书相关信息list
legal_document_list = StructuredTool.from_function(
    func=get_legal_document_list,
    name="get_legal_document_list",
    args_schema=keyValue,
    description="""
    根据`关联公司`查询所有裁判文书相关信息list。
    相关信息包含关联公司，标题，案号，文书类型，原告，被告，原告律师事务所，被告律师事务所，案由，涉案金额，判决结果，日期，文件名。
    """,
)

# 根据案号查询文本摘要
legal_document_abstract = StructuredTool.from_function(
    func=get_legal_abstract,
    name="get_legal_abstract",
    args_schema=keyValue,
    description="""
    根据`案号`查询文本摘要，其中案号一般是形如："(2019)沪0115民初61975号。
    文本摘要包含文件名，案号，文本摘要。
    """
)

# 根据案号查询限制高消费相关信息
legal_document_axzgxf_info = StructuredTool.from_function(
    func=get_xzgxf_info,
    name="get_xzgxf_info",
    args_schema=keyValue,
    description="""
    根据`案号`查询限制高消费相关信息，其中案号一般是形如："(2019)沪0115民初61975号。
    相关信息包含限制高消费企业名称，案号，法定代表人，申请人，涉案金额，执行法院，立案日期，限高发布日期。
    """
)

# 关于法律文书的工具集合
legal_instrument_tools = [
    legal_document_info_getter,
    legal_document_list,
    legal_document_abstract,
    legal_document_axzgxf_info,
]
