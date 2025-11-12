# https://docs.langchain.com/oss/python/langgraph/workflows-agents#parallelization 
# 通过并行化，LLM（逻辑逻辑管理器）可以同时处理同一任务。这可以通过同时运行多个独立的子任务，或者多次运行同一任务以检查不同的输出来实现。并行化通常用于：
# 将子任务拆分并并行运行，这样可以提高速度。
# 多次运行任务以检查不同的输出，这可以提高置信度。
# 例如：
# 运行一个子任务来处理文档中的关键词，以及第二个子任务来检查格式错误。
# 多次运行一项任务，该任务根据不同的标准（例如引用次数、使用的来源数量和来源质量）对文档的准确性进行评分。

from ChatOpenAIModel_LangChian import model
from langgraph.func import entrypoint, task


llm = model


@task
def call_llm_1(topic: str):
    """First LLM call to generate initial joke"""
    msg = llm.invoke(f"Write a joke about {topic}")
    return msg.content


@task
def call_llm_2(topic: str):
    """Second LLM call to generate story"""
    msg = llm.invoke(f"Write a story about {topic}")
    return msg.content


@task
def call_llm_3(topic):
    """Third LLM call to generate poem"""
    msg = llm.invoke(f"Write a poem about {topic}")
    return msg.content


@task
def aggregator(topic, joke, story, poem):
    """Combine the joke and story into a single output"""

    combined = f"Here's a story, joke, and poem about {topic}!\n\n"
    combined += f"STORY:\n{story}\n\n"
    combined += f"JOKE:\n{joke}\n\n"
    combined += f"POEM:\n{poem}"
    return combined


# Build workflow
@entrypoint()
def parallel_workflow(topic: str):
    joke_fut = call_llm_1(topic)
    story_fut = call_llm_2(topic)
    poem_fut = call_llm_3(topic)
    return aggregator(
        topic, joke_fut.result(), story_fut.result(), poem_fut.result()  # 对应的任务函数后面跟着 result() 才会执行
    ).result()


# Invoke
for step in parallel_workflow.stream("cats", stream_mode="updates"):
    print(step)
    print("\n")
