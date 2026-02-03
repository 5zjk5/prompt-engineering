# 副作用（写入文件）直接包含在工作流中，因此在恢复工作流时会再次执行
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # This code will be executed a second time when resuming the workflow.
    # Which is likely not what you want.
    with open("output.txt", "w") as f:  
        f.write("Side effect executed")  
    value = interrupt("question")
    return value

# 副作用被封装在一个任务中，确保在恢复时能够一致地执行。
from langgraph.func import task

@task
def write_to_file():  
    with open("output.txt", "w") as f:
        f.write("Side effect executed")

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # The side effect is now encapsulated in a task.
    write_to_file().result()
    value = interrupt("question")
    return value



# 在使用包含多次中断调用的人工参与工作流时，这一点尤为重要。
# LangGraph 为每个任务/入口点维护一个恢复值列表。当遇到中断时，它会与相应的恢复值进行匹配。
# 这种匹配严格基于索引，因此恢复值的顺序应与中断的顺序一致。
# 每次执行可能产生不同结果的操作（例如获取当前时间或随机数）应封装在任务中，以确保恢复执行时返回相同的结果。
from langgraph.func import entrypoint

# 错误
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = time.time()  

    delta_t = t1 - t0

    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")

    return {
        "result": result,
        "value": value
    }


# 工作流利用输入t0来确定要执行的任务。这是确定性的，因为工作流的结果仅取决于输入。
# 正确
import time

from langgraph.func import task

@task
def get_time() -> float:  
    return time.time()

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = get_time().result()  

    delta_t = t1 - t0

    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")

    return {
        "result": result,
        "value": value
    }
