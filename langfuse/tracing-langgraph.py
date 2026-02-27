# https://docs.langchain.com/oss/python/integrations/providers/langfuse#view-traces-in-langfuse
"""
langgraphy最基本使用
"""

import os
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv as load_env


# Load environment variables
load_env()


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

llm = ChatOpenAI(
    model=os.getenv('model'),
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key'),
)

# The chatbot node function takes the current State as input and returns an updated messages list. This is the basic pattern for all LangGraph node functions.
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# Add a "chatbot" node. Nodes represent units of work. They are typically regular python functions.
graph_builder.add_node("chatbot", chatbot)

# Add an entry point. This tells our graph where to start its work each time we run it.
graph_builder.set_entry_point("chatbot")

# Set a finish point. This instructs the graph "any time this node is run, you can exit."
graph_builder.set_finish_point("chatbot")

# To be able to run our graph, call "compile()" on the graph builder. This creates a "CompiledGraph" we can use invoke on our state.
graph = graph_builder.compile()

# Initialize Langfuse CallbackHandler for LangChain (tracing)
langfuse_handler = CallbackHandler()

for s in graph.stream({"messages": [HumanMessage(content = "介绍你自己")]},
                      config={"callbacks": [langfuse_handler]}):
    print(s)
