# LangGraph 支持根据节点的输入缓存任务/节点。要使用缓存：
# 编译图时（或指定入口点时）指定缓存
# 为节点指定缓存策略。每个缓存策略支持：
# key_func用于根据节点的输入生成缓存键，默认为hashpickle 输入。
# ttl缓存的生存时间（以秒为单位）。如果未指定，则缓存永不过期。

import time
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy


class State(TypedDict):
    x: int
    result: int


builder = StateGraph(State)


def expensive_node(state: State) -> dict[str, int]:
    # expensive computation
    time.sleep(2)
    return {"result": state["x"] * 2}


builder.add_node("expensive_node", expensive_node, cache_policy=CachePolicy(ttl=3))
builder.set_entry_point("expensive_node")
builder.set_finish_point("expensive_node")

graph = builder.compile(cache=InMemoryCache())

print(graph.invoke({"x": 5}, stream_mode='updates'))    
# [{'expensive_node': {'result': 10}}]
print(graph.invoke({"x": 5}, stream_mode='updates'))    
# [{'expensive_node': {'result': 10}, '__metadata__': {'cached': True}}]

