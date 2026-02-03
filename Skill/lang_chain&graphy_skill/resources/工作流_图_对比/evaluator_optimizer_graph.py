# https://docs.langchain.com/oss/python/langgraph/workflows-agents#evaluator-optimizer
# 在评估器-优化器工作流程中，一个LLM调用生成响应，另一个调用评估该响应。如果评估器或人工参与判断认为响应需要改进，则会提供反馈并重新生成响应。此循环持续进行，直至生成可接受的响应。
# 当任务有特定的成功标准，但需要迭代才能满足这些标准时，通常会使用评估器-优化器工作流程。例如，在两种语言之间翻译文本时，并非总能找到完美匹配的译文。可能需要多次迭代才能生成在两种语言中含义相同的译文。

from ChatOpenAIModel_LangChian import model
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from IPython.display import Image, display


llm = model


# Graph state
class State(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str


# Schema for structured output to use in evaluation
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="Decide if the joke is funny or not.",
    )
    feedback: str = Field(
        description="If the joke is not funny, provide feedback on how to improve it.",
    )


# Augment the LLM with schema for structured output
evaluator = llm.with_structured_output(Feedback)


# Nodes
def llm_call_generator(state: State):
    """LLM generates a joke"""

    if state.get("feedback"):
        msg = llm.invoke(
            f"Write a joke about {state['topic']} but take into account the feedback: {state['feedback']}"
        )
    else:
        msg = llm.invoke(f"Write a joke about {state['topic']}")
    return {"joke": msg.content}


def llm_call_evaluator(state: State):
    """LLM evaluates the joke"""

    grade = evaluator.invoke(f"Grade the joke {state['joke']}")
    return {"funny_or_not": grade.grade, "feedback": grade.feedback}


# Conditional edge function to route back to joke generator or end based upon feedback from the evaluator
def route_joke(state: State):
    """Route back to joke generator or end based upon feedback from the evaluator"""

    if state["funny_or_not"] == "funny":
        return "Accepted"
    elif state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"


# Build workflow
optimizer_builder = StateGraph(State)

# Add the nodes
optimizer_builder.add_node("llm_call_generator", llm_call_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

# Add edges to connect nodes
optimizer_builder.add_edge(START, "llm_call_generator")
optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_joke,
    {  # Name returned by route_joke : Name of next node to visit
        "Accepted": END,
        "Rejected + Feedback": "llm_call_generator",
    },
)

# Compile the workflow
optimizer_graph = optimizer_builder.compile()

# Show the workflow
display(Image(optimizer_graph.get_graph().draw_mermaid_png()))
png_data = optimizer_graph.get_graph().draw_mermaid_png()
filename = "evaluator_optimizer_graph.png"
with open(filename, "wb") as f:
    f.write(png_data)

# Invoke
state = optimizer_graph.invoke({"topic": "Cats"})
print(state["joke"])
