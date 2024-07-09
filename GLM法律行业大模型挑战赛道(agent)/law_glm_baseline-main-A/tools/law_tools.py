from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool

from services.law_service import *


class CaseNumInput(BaseModel):
    case_num: str = Field(description="案号")


class CauseOfActionInput(BaseModel):
    cause_of_action: str = Field(description="案由")


class PlaintiffInput(BaseModel):
    plaintiff: str = Field(description="原告")


class DefendantInput(BaseModel):
    defendant: str = Field(description="被告")


class KeyValueInput(BaseModel):
    key: str = Field(description="键")
    value: str = Field(description="值")


# 根据案号获得该案的涉案金额。
amount_involved_getter = StructuredTool.from_function(
    func=get_amount_involved_by_case_num_service,
    name="amount_involved_getter",
    args_schema=CaseNumInput,
)
"""根据案号获得该案所有基本信息，包括'判决结果','原告','原告律师','审理法条依据',
    '文书类型','文件名','标题','案由','涉案金额','胜诉方','被告','被告律师'。"""
legal_document_getter = StructuredTool.from_function(
    func=get_legal_document_service,
    name="legal_document_getter",
    description="""
    根据案号获得该案所有基本信息，包括'判决结果','原告','原告律师','审理法条依据',
    '文书类型','文件名','标题','案由','涉案金额','胜诉方','被告','被告律师'。
    """,
    args_schema=CaseNumInput,
)
# 根据案由获得涉及该案由的案件数量。
case_number_counter_by_cause = StructuredTool.from_function(
    func=count_case_number_by_cause_service,
    name="case_number_counter_by_cause",
    args_schema=CauseOfActionInput,
)
"""  根据法律文书某个 key 是某个 value 来查询具体的案号。这个函数只能用来查询案号。
    可以输入的 key 有['判决结果','原告','原告律师','审理法条依据',
    '文书类型','文件名','标题','案由','涉案金额','胜诉方','被告','被告律师']"""
case_num_retriever_by_legal_document = StructuredTool.from_function(
    func=search_case_num_by_legal_document_service,
    name="case_num_retriever_by_legal_document",
    args_schema=KeyValueInput,
)
# 发起诉讼担任原告时，统计公司聘请的不同原告律师的频次。
plaintiff_lawyer_counter = StructuredTool.from_function(
    func=count_plaintiff_lawyer_service,
    name="plaintiff_lawyer_counter",
    args_schema=PlaintiffInput,
)
# 面临诉讼担任被告时，统计公司聘请的不同被告律师的频次。
defendant_lawyer_counter = StructuredTool.from_function(
    func=count_defendant_lawyer_service,
    name="defendant_lawyer_counter",
    args_schema=DefendantInput,
)

law_tools = [
    amount_involved_getter,
    legal_document_getter,
    case_number_counter_by_cause,
    case_num_retriever_by_legal_document,
    plaintiff_lawyer_counter,
    defendant_lawyer_counter,
]
