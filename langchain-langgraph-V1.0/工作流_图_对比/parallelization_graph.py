# https://docs.langchain.com/oss/python/langgraph/workflows-agents#parallelization 
# 通过并行化，LLM（逻辑逻辑管理器）可以同时处理同一任务。这可以通过同时运行多个独立的子任务，或者多次运行同一任务以检查不同的输出来实现。并行化通常用于：
# 将子任务拆分并并行运行，这样可以提高速度。
# 多次运行任务以检查不同的输出，这可以提高置信度。
# 例如：
# 运行一个子任务来处理文档中的关键词，以及第二个子任务来检查格式错误。
# 多次运行一项任务，该任务根据不同的标准（例如引用次数、使用的来源数量和来源质量）对文档的准确性进行评分。

from ChatOpenAIModel_LangChian import model
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display


llm = model


# Graph state
class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str


# Nodes
def call_llm_1(state: State):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(f"Write a joke about {state['topic']}")
    return {"joke": msg.content}


def call_llm_2(state: State):
    """Second LLM call to generate story"""

    msg = llm.invoke(f"Write a story about {state['topic']}")
    return {"story": msg.content}


def call_llm_3(state: State):
    """Third LLM call to generate poem"""

    msg = llm.invoke(f"Write a poem about {state['topic']}")
    return {"poem": msg.content}


def aggregator(state: State):
    """Combine the joke and story into a single output"""

    combined = f"Here's a story, joke, and poem about {state['topic']}!\n\n"
    combined += f"STORY:\n{state['story']}\n\n"
    combined += f"JOKE:\n{state['joke']}\n\n"
    combined += f"POEM:\n{state['poem']}"
    return {"combined_output": combined}


# Build workflow
parallel_builder = StateGraph(State)

# Add nodes
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# Add edges to connect nodes
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
parallel_builder.add_edge("aggregator", END)
parallel_workflow = parallel_builder.compile()

# Show workflow
display(Image(parallel_workflow.get_graph().draw_mermaid_png()))
# 生成图片并保存
png_data = parallel_workflow.get_graph().draw_mermaid_png()
filename = "parallel_graph.png"
with open(filename, "wb") as f:
    f.write(png_data)

# Invoke
state = parallel_workflow.invoke({"topic": "cats"})
print(state["combined_output"])
