from typing_extensions import TypedDict
from langgraph.graph import MessagesState
from typing import Annotated, Optional
from operator import add
from langchain_core.messages import MessageLikeRepresentation
from pydantic import BaseModel, Field


###################
# State Definitions
###################
def override_reducer(current_value, new_value):
    """
    允许在状态中覆盖值的归约器函数

    例如：
        return Command(
            goto="research_supervisor", 
            update={
                "research_brief": response.research_brief,
                "supervisor_messages": {
                    "type": "override",
                    "value": [
                        SystemMessage(content=supervisor_system_prompt),
                        HumanMessage(content=response.research_brief)
                    ]
                }
            }
        )
        supervisor_messages 值更新时，如果定义字段中定义了这个函数，那 update 时都会调用，如：
        supervisor_messages: Annotated[list[MessageLikeRepresentation], override_reducer]
        current_value：当前已存在的值
        new_value 当前 update 的值
    """
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)  # 覆盖
    else:
        return add(current_value, new_value)  # 更新合并


class AgentState(MessagesState):
    """主代理状态，包含消息和研究数据"""
    supervisor_messages: Annotated[list[MessageLikeRepresentation], override_reducer]
    research_brief: Optional[str]
    raw_notes: Annotated[list[str], override_reducer]
    notes: Annotated[list[str], override_reducer]
    final_report: str


class AgentInputState(MessagesState):
    """主代理输入为 'messages'."""


class SupervisorState(TypedDict):
    """研究主观说明研究任务，指导研究方向"""
    supervisor_messages: Annotated[list[MessageLikeRepresentation], override_reducer]
    research_brief: str
    notes: Annotated[list[str], override_reducer]
    research_iterations: int
    raw_notes: Annotated[list[str], override_reducer]


class ResearcherState(TypedDict):
    """为个别研究人员进行的研究。即调用搜索工具去研究"""
    researcher_messages: Annotated[list[MessageLikeRepresentation], add]
    tool_call_iterations: int
    research_topic: str
    compressed_research: str
    raw_notes: Annotated[list[str], override_reducer]


class ResearcherOutputState(BaseModel):
    """研究人员分别输出的状态。"""
    compressed_research: str
    raw_notes: Annotated[list[str], override_reducer] = []


###################
# Structured Outputs
###################
class ClarifyWithUser(BaseModel):
    """用户澄清请求格式化输出字段"""
    need_clarification: bool = Field(
        description="是否用户需要询问澄清问题",
    )
    question: str = Field(
        description="用户需要询问的澄清问题",
    )
    verification: str = Field(
        description="用户提供必要信息后，我们将开始研究的确认消息",
    )


class ResearchQuestion(BaseModel):
    """研究计划，研究方向格式化输出字段"""
    research_brief: str = Field(
        description="研究计划，研究方向，用于指导研究",
    )


class Summary(BaseModel):
    """研究总结和关键发现。"""
    summary: str
    key_excerpts: str
