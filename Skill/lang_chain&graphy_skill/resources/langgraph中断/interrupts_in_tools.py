# https://docs.langchain.com/oss/python/langgraph/interrupts#interrupts-in-tools
# 您还可以直接在工具函数内部放置中断。这样，每次调用工具时，工具本身都会暂停以等待批准，从而允许在执行工具调用之前进行人工审核和编辑

import sqlite3
from typing import TypedDict

from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class AgentState(TypedDict):
    messages: list[dict]


@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""

    # Pause before sending; payload surfaces in result["__interrupt__"]
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?",
    })

    if response.get("action") == "approve":
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)

        # Actually send the email (your implementation here)
        print(f"[send_email] to={final_to} subject={final_subject} body={final_body}")
        return f"Email sent to {final_to}"

    return "Email cancelled by user"


model = ChatAnthropic(model="claude-sonnet-4-5-20250929").bind_tools([send_email])


def agent_node(state: AgentState):
    # LLM may decide to call the tool; interrupt pauses before sending
    result = model.invoke(state["messages"])
    return {"messages": state["messages"] + [result]}


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

checkpointer = SqliteSaver(sqlite3.connect("tool-approval.db"))
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "email-workflow"}}
initial = graph.invoke(
    {
        "messages": [
            {"role": "user", "content": "Send an email to alice@example.com about the meeting"}
        ]
    },
    config=config,
)
print(initial["__interrupt__"])  # -> [Interrupt(value={'action': 'send_email', ...})]

# Resume with approval and optionally edited arguments
resumed = graph.invoke(
    Command(resume={"action": "approve", "subject": "Updated subject"}),
    config=config,
)
print(resumed["messages"][-1])  # -> Tool result returned by send_email
