from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool

from services.company_register_service import *


class CompanyNameInput(BaseModel):
    company_name: str = Field(description="公司名称")


class IndustryNameInput(BaseModel):
    industry_name: str = Field(description="行业名称")


class RegistrationNumberInput(BaseModel):
    registration_number: str = Field(description="注册号")


class KeyValueInput(BaseModel):
    key: str = Field(description="键")
    value: str = Field(description="值")


# 根据公司名称，获得该公司所有注册信息。
company_register_getter = StructuredTool.from_function(
    func=get_company_register_service,
    name="company_register_getter",
    args_schema=CompanyNameInput,
)
# 根据注册号查询公司名称。
company_name_retriever_by_register_number = StructuredTool.from_function(
    func=search_company_name_by_registration_number_service,
    name="company_name_retriever_by_register_number",
    args_schema=RegistrationNumberInput,
)
# 根据公司注册信息 key 是某个 value 来查询具体的公司名称。
company_name_retriever_by_register = StructuredTool.from_function(
    func=search_company_name_by_register_service,
    name="company_name_retriever_by_register",
    args_schema=KeyValueInput,
)
# 根据行业名称查询属于该行业的公司及其注册资本。
cnr_retriever_by_industry = StructuredTool.from_function(
    func=search_cnr_by_industry_service,
    name="cnr_retriever_by_industry",
    args_schema=IndustryNameInput,
)

com_register_tools = [
    company_register_getter,
    company_name_retriever_by_register_number,
    company_name_retriever_by_register,
    cnr_retriever_by_industry,
]
