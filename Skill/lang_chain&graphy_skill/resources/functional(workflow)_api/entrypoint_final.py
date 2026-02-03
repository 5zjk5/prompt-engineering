# entrypoint.final是一个特殊的原始值，可以从入口点返回，它允许将保存在检查点中的值与入口点的返回值解耦。
# 第一个值是入口点的返回值，第二个值是将保存到检查点中的值。类型注解为entrypoint.final[return_type, save_type]。
# 有点像递归

from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any


checkpointer = InMemorySaver()



@entrypoint(checkpointer=checkpointer)
def my_workflow(number: int, *, previous: Any = None) -> entrypoint.final[int, int]:
    previous = previous or 0
    # This will return the previous value to the caller, saving
    # 2 * number to the checkpoint, which will be used in the next invocation
    # for the `previous` parameter.
    return entrypoint.final(value=previous, save=2 * number)

config = {
    "configurable": {
        "thread_id": "1"
    }
}

print(my_workflow.invoke(3, config))  # 0 (previous was None)
print(my_workflow.invoke(1, config))  # 6 (previous was 3 * 2 from the previous invocation)
