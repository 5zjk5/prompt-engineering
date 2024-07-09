from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool

from services.company_info_service import *


class CompanyNameInput(BaseModel):
    company_name: str = Field(description="公司名称")


class IndustryNameInput(BaseModel):
    industry_name: str = Field(description="行业名称")


class KeyValueInput(BaseModel):
    key: str = Field(description="键")
    value: str = Field(description="值")


# 根据公司名称，获得该公司所有基本信息。
company_info_getter = StructuredTool.from_function(
    func=get_company_info_service,
    name="company_info_getter",
    args_schema=CompanyNameInput,
)
# 根据所属行业，统计该行业下公司的数量。
company_counter_by_industry = StructuredTool.from_function(
    func=count_company_by_industry_service,
    name="company_counter_by_industry",
    args_schema=IndustryNameInput,
)
# 根据公司基本信息某个字段是某个值来查询具体的公司名称。
company_name_retriever_by_info = StructuredTool.from_function(
    func=search_company_name_by_info_service,
    name="company_name_retriever_by_info",
    args_schema=KeyValueInput,
)

com_info_tools = [
    company_info_getter,
    company_counter_by_industry,
    company_name_retriever_by_info,
]
