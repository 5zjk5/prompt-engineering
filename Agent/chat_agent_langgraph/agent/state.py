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


class AgentInputState(MessagesState):
    """主代理输入为 'messages'."""


class AgentState(MessagesState):
    """主代理状态，包含消息和研究数据"""
    supervisor_messages: Annotated[list[MessageLikeRepresentation], override_reducer]
    research_brief: Optional[str]
    raw_notes: Annotated[list[str], override_reducer]
    notes: Annotated[list[str], override_reducer]
    final_report: str
