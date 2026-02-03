# https://docs.langchain.com/oss/python/langgraph/use-time-travel#setup

import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from ChatOpenAIModel_LangChian import model


class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]


def generate_topic(state: State):
    """LLM call to generate a topic for the joke"""
    msg = model.invoke("Give me a funny topic for a joke")
    return {"topic": msg.content}


def write_joke(state: State):
    """LLM call to write a joke based on the topic"""
    msg = model.invoke(f"Write a short joke about {state['topic']}")
    return {"joke": msg.content}


# Build workflow
workflow = StateGraph(State)

# Add nodes
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_joke", write_joke)

# Add edges to connect nodes
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_joke")
workflow.add_edge("write_joke", END)

# Compile
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)


# 运行
config = {
    "configurable": {
        "thread_id": uuid.uuid4(),
    }
}
state = graph.invoke({}, config)
print(state["topic"])
print()
print(state["joke"])


# 检查所有检查点
# 逆序打印
states = list(graph.get_state_history(config))
for state in states:
    print(state.next)
    print(state.config["configurable"]["checkpoint_id"])
    print()
# This is the state before last (states are listed in chronological order)
selected_state = states[1]  # 选中
print(selected_state.next)
print(selected_state.values)



# update_state将创建一个新的检查点。新检查点将与同一线程关联，但具有新的检查点 ID。
new_config = graph.update_state(selected_state.config, values={"topic": "chickens"})
print(new_config)



# 从检查点恢复执行
state = graph.invoke(None, new_config)
print(state["topic"])
print()
print(state["joke"])
