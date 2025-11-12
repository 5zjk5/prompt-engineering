from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool

from services.sub_company_info_service import *


class CompanyNameInput(BaseModel):
    company_name: str = Field(description="公司名称")


class KeyValueInput(BaseModel):
    key: str = Field(description="键")
    value: str = Field(description="值")


#    根据子公司的公司名称，查询该公司的母公司信息，或者说查询该公司是哪家公司旗下的子公司。
#    母公司信息包括'母公司名称'、'母公司参股比例'、'母公司投资金额'。
parent_company_info_getter = StructuredTool.from_function(
    func=get_parent_company_info_service,
    name="parent_company_info_getter",
    args_schema=CompanyNameInput,
)
# 根据母公司的公司名称，获得该公司旗下的所有子公司的名称。
sub_company_name_getter = StructuredTool.from_function(
    func=get_sub_company_name_service,
    name="sub_company_name_getter",
    args_schema=CompanyNameInput,
)

# 根据母公司的公司名称，获得该公司的所有子公司、投资对象的信息。
# 包括'上市公司关系'、'上市公司参股比例'、'上市公司投资金额'、'公司名称'、'关联上市公司全称'，
# 值得注意的是关联上市公司是该公司的名称，公司名称是该公司的子公司的名称。
sub_company_info_getter = StructuredTool.from_function(
    func=get_sub_company_info_service,
    name="sub_company_info_getter",
    args_schema=CompanyNameInput,
)
# 根据母公司的公司名称，统计该公司所有子公司的数量。
all_sub_company_counter = StructuredTool.from_function(
    func=count_sub_company_service,
    name="all_sub_company_counter",
    args_schema=CompanyNameInput,
)

"""根据关联上市公司信息某个字段是某个值来查询具体的公司名称。
    可以输入的字段有['上市公司关系','上市公司参股比例','上市公司投资金额','关联上市公司全称',
    '关联上市公司股票代码','关联上市公司股票简称']"""
company_name_retriever_by_super_info = StructuredTool.from_function(
    func=search_company_name_by_super_info_service,
    name="company_name_retriever_by_super_info",
    args_schema=KeyValueInput,
)
"""根据上市公司的公司名称、公司简称或英文名称，查询该公司在子公司投资的总金额。"""
total_amount_invested_in_subsidiaries_getter = StructuredTool.from_function(
    func=query_total_amount_invested_in_subsidiaries,
    name="total_amount_invested_in_subsidiaries_getter",
    args_schema=CompanyNameInput,
)

get_listed_company_info_getter = StructuredTool.from_function(
    func=get_listed_company_info,
    name="get_listed_company_info_getter",
    args_schema=CompanyNameInput,
)

"""根据上市公司的公司名称、公司简称或英文名称，查询该公司在子公司投资的总金额。"""
total_amount_fully_owned_getter = StructuredTool.from_function(
    func=query_total_amount_fully_owned,
    name="total_amount_fully_owned_getter",
    args_schema=CompanyNameInput,
)

query_total_amount_half_owned_investment_getter = StructuredTool.from_function(
    func=query_total_amount_half_owned_investment,
    name="query_total_amount_half_owned_investment_getter",
    args_schema=CompanyNameInput,
)
query_total_amount_half_owned_getter = StructuredTool.from_function(
    func=query_total_amount_half_owned,
    name="query_total_amount_half_owned_getter",
    args_schema=CompanyNameInput,
)


sub_com_info_tools = [
    get_listed_company_info_getter,
    parent_company_info_getter,
    sub_company_name_getter,
    sub_company_info_getter,
    company_name_retriever_by_super_info,
    total_amount_invested_in_subsidiaries_getter,
    total_amount_fully_owned_getter,
    query_total_amount_half_owned_getter,
    query_total_amount_half_owned_investment_getter,
    all_sub_company_counter
]
