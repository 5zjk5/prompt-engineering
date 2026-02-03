# https://docs.langchain.com/oss/python/langgraph/add-memory#trim-messages
# 相当于调模型之前使用了现成的封装函数 trim_messages
from langchain_core.messages.utils import (  
    trim_messages,  
    count_tokens_approximately  
)  

def call_model(state: MessagesState):
    messages = trim_messages(  
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node(call_model)
...


# https://docs.langchain.com/oss/python/langgraph/add-memory#delete-messages
# 跟 langchain 一样


# https://docs.langchain.com/oss/python/langgraph/add-memory#summarize-messages
# 使用了封装函数 SummarizationNode，单独作为一个节点
from langmem.short_term import SummarizationNode, RunningSummary  

class State(MessagesState):
    context: dict[str, RunningSummary]  

class LLMInputState(TypedDict):  
    summarized_messages: list[AnyMessage]
    context: dict[str, RunningSummary]

summarization_node = SummarizationNode(  
    token_counter=count_tokens_approximately,
    model=summarization_model,
    max_tokens=256,
    max_tokens_before_summary=256,
    max_summary_tokens=128,
)

...
builder.add_node("summarize", summarization_node)  
...
