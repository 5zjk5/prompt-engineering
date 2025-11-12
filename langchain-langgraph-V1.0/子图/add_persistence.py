# https://docs.langchain.com/oss/python/langgraph/use-subgraphs#add-persistence

from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

class State(TypedDict):
    foo: str

# Subgraph

def subgraph_node_1(state: State):
    return {"foo": state["foo"] + "bar"}

subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()

# Parent graph

builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)  # 提供检查点

# 如果您希望子图拥有自己的内存，可以使用相应的检查点选项进行编译。这在多智能体系统中非常有用，如果您希望智能体跟踪其内部消息历史记录：
subgraph_builder = StateGraph(...)
subgraph = subgraph_builder.compile(checkpointer=True)
