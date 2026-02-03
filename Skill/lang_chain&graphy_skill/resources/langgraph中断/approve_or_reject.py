# https://docs.langchain.com/oss/python/langgraph/interrupts#approve-or-reject
# 中断最常见的用途之一是在执行关键操作前暂停并请求批准。例如，您可能需要请人批准 API 调用、数据库更改或任何其他重要决策。

import operator
from typing import Literal, Optional, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from typing import Annotated


class ApprovalState(TypedDict):
    action_details: str
    status: Annotated[Literal["pending", "approved", "rejected"], operator.add]


def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
    # Expose details so the caller can render them in a UI
    # Pause execution; payload shows up under result["__interrupt__"]
    decision = interrupt({
        "question": "Approve this action?",
        "details": state["action_details"],
    })

    # Route to the appropriate node after resume
    return Command(goto="proceed" if decision else "cancel")


def proceed_node(state: ApprovalState):
    return {"status": "approved"}


def cancel_node(state: ApprovalState):
    return {"status": "rejected"}


builder = StateGraph(ApprovalState)
builder.add_node("approval", approval_node)
builder.add_node("proceed", proceed_node)
builder.add_node("cancel", cancel_node)
builder.add_edge(START, "approval")
builder.add_edge("approval", "proceed")
builder.add_edge("approval", "cancel")
builder.add_edge("proceed", END)
builder.add_edge("cancel", END)

# Use a more durable checkpointer in production
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "approval-123"}}
initial = graph.invoke(
    {"action_details": "Transfer $500", "status": "pending"},
    config=config,
)
print(initial["__interrupt__"])  # -> [Interrupt(value={'question': ..., 'details': ...})]

# Resume with the decision; True routes to proceed, False to cancel
resumed = graph.invoke(Command(resume=False), config=config)
print(resumed["status"])  # -> "approved"


# To approve
# graph.invoke(Command(resume=True), config=config)

# # To reject
# graph.invoke(Command(resume=False), config=config)