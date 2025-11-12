# https://docs.langchain.com/oss/python/langgraph/workflows-agents#evaluator-optimizer
# 在评估器-优化器工作流程中，一个LLM调用生成响应，另一个调用评估该响应。如果评估器或人工参与判断认为响应需要改进，则会提供反馈并重新生成响应。此循环持续进行，直至生成可接受的响应。
# 当任务有特定的成功标准，但需要迭代才能满足这些标准时，通常会使用评估器-优化器工作流程。例如，在两种语言之间翻译文本时，并非总能找到完美匹配的译文。可能需要多次迭代才能生成在两种语言中含义相同的译文。

from ChatOpenAIModel_LangChian import model
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.func import entrypoint, task


llm = model


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
@task
def llm_call_generator(topic: str, feedback: Feedback):
    """LLM generates a joke"""
    if feedback:
        msg = llm.invoke(
            f"Write a joke about {topic} but take into account the feedback: {feedback}"
        )
    else:
        msg = llm.invoke(f"Write a joke about {topic}")

    return msg.content


@task
def llm_call_evaluator(joke: str):
    """LLM evaluates the joke"""
    feedback = evaluator.invoke(f"Grade the joke {joke}")
    return feedback


@entrypoint()
def optimizer_workflow(topic: str):
    feedback = None
    while True:
        joke = llm_call_generator(topic, feedback).result()
        feedback = llm_call_evaluator(joke).result()
        if feedback.grade == "funny":
            break

    return joke


# Invoke
for step in optimizer_workflow.stream("Cats", stream_mode="updates"):
    print(step)
    print("\n")
