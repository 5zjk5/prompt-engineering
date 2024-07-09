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


# 根据上市公司名称、简称或代码查找上市公司信息
company_info_getter = StructuredTool.from_function(
    func=get_company_info,
    name="company_info_getter",
    args_schema=keyValue,
    description="""
    根据上市`公司名称`或`公司代码`或`公司简称`查找上市公司信息。
    公司信息包含公司名称，公司简称，英文名称，关联证券，公司代码，曾用简称，所属市场，所属行业，成立日期，上市日期，法人代表，总经理，董秘，邮政编码，
    注册地址，办公地址，联系电话，传真，官方网址，电子邮箱，入选指数，主营业务，经营范围，机构简介，每股面值，首发价格，首发募资净额，首发主承销商。
    """
)

# 根据公司名称，查询工商信息
company_register_info = StructuredTool.from_function(
    func=get_company_register,
    name="get_company_register",
    args_schema=keyValue,
    description="""
    根据`公司名称`，查询工商信息。
    工商信息包含公司名称，登记状态，统一社会信用代码，法定代表人，注册资本，成立日期，企业地址，联系电话，联系邮箱，注册号，组织机构代码，参保人数，
    行业一级，行业二级，行业三级，曾用名，企业简介，经营范围。
    """
)

# 根据统一社会信用代码查询公司名称
company_name_by_credit_code = StructuredTool.from_function(
    func=get_company_register_name,
    name="get_company_register_name",
    args_schema=keyValue,
    description="""
    根据`统一社会信用代码`查询公司名称，社会信用代码格式一般为18位数字，前17位为组织机构代码，最后一位为校验码，校验码为数字或大写字母。例如：
    91310000677833266F，913305007490121183
    """,
    infer_schema=True
)

# 根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息
sub_company_info = StructuredTool.from_function(
    func=get_sub_company_info,
    name="get_sub_company_info",
    args_schema=keyValue,
    description="""
    根据被投资的子`公司名称`获得投资该公司的上市公司、投资比例、投资金额等相关信息。
    如果`公司名称`判断为简称，需要先获得`公司名称`。
    相关信息包含关联上市公司全称，上市公司关系，上市公司参股比例，上市公司投资金额，公司名称。
    """
)

# 根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list
sub_company_info_list = StructuredTool.from_function(
    func=get_sub_company_info_list,
    name="get_sub_company_info",
    args_schema=keyValue,
    description="""
    根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list。
    如果`关联上市公司`全称判断为简称，需要先获得公司名称·。
    子公司信息包含关联上市公司全称，上市公司关系，上市公司参股比例，上市公司投资金额，公司名称。
    """
)


# 根据企业名称查询所有限制高消费相关信息list
xzgxf_info_list = StructuredTool.from_function(
    func=get_xzgxf_info_list,
    name="get_xzgxf_info_list",
    args_schema=keyValue,
    description="""
    根据`限制高消费企业名称`查询限制高消费相关信息list，如果企业名称（公司名称）判断为`公司简称`，需要先获得`公司名称`全名。
    相关信息包含限制高消费企业名称，案号，法定代表人，申请人，涉案金额，执行法院，立案日期，限高发布日期。
    """
)

# 关于公司的工具集合
com_info_tools = [
    company_info_getter,
    company_register_info,
    company_name_by_credit_code,
    sub_company_info,
    sub_company_info_list,
    xzgxf_info_list
]
