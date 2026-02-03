# 覆盖状态
# 在某些情况下，您可能需要绕过 reducer 并直接覆盖状态值。
# LangGraphOverwrite为此提供了相应的类型。当节点返回一个用 `@Reducer` 包装的值时Overwrite，reducer 将被绕过，通道将直接设置为该值。
# 当您想要重置或替换累积状态而不是将其与现有值合并时，此功能非常有用。

from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite
from typing_extensions import Annotated, TypedDict
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

def add_message(state: State):
    return {"messages": ["first message"]}

def replace_messages(state: State):
    # Bypass the reducer and replace the entire messages list
    return {"messages": Overwrite(["replacement message"])}

builder = StateGraph(State)
builder.add_node("add_message", add_message)
builder.add_node("replace_messages", replace_messages)
builder.add_edge(START, "add_message")
builder.add_edge("add_message", "replace_messages")
builder.add_edge("replace_messages", END)

graph = builder.compile()

result = graph.invoke({"messages": ["initial"]})
print(result["messages"])
