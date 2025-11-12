# https://docs.langchain.com/oss/python/langgraph/graph-api#multiple-schemas
# 用于节点内部通信。我们可以简单地定义一个私有模式PrivateState。
# 也可以为图定义显式的输入和输出模式。在这种情况下，我们会定义一个“内部”模式，其中包含所有与图操作相关的键。
# 此外，我们还会定义一些input子模式，output这些子模式是“内部”模式的子集，用于约束图的输入和输出
# 只要状态模式定义存在，就默认会传递

from langgraph.graph import START, StateGraph, END
from typing_extensions import TypedDict

class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class OverallState(TypedDict):
    foo: str
    user_input: str
    graph_output: str

class PrivateState(TypedDict):
    bar: str

def node_1(state: InputState) -> OverallState:
    # Write to OverallState
    return {"foo": state["user_input"] + " name"}

def node_2(state: OverallState) -> PrivateState:
    # Read from OverallState, write to PrivateState
    return {"bar": state["foo"] + " is"}

def node_3(state: PrivateState) -> OutputState:
    # Read from PrivateState, write to OutputState
    return {"graph_output": state["bar"] + " Lance"}

builder = StateGraph(OverallState,input_schema=InputState,output_schema=OutputState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
graph.invoke({"user_input":"My"})
# {'graph_output': 'My name is Lance'}