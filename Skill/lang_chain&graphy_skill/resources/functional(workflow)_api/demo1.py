# 此工作流程会先撰写一篇关于“猫”的文章，然后暂停以获取人工审阅。在收到审阅之前，工作流程可能会无限期中断。
# 当工作流恢复时，它会从头开始执行，但由于任务结果writeEssay已经保存，因此将从检查点加载任务结果，而不是重新计算。

import time
import uuid
from langgraph.func import entrypoint, task
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver


@task
def write_essay(topic: str) -> str:
    """Write an essay about the given topic."""
    time.sleep(1)  # This is a placeholder for a long-running task.
    return f"An essay about topic: {topic}"

@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    """A simple workflow that writes an essay and asks for a review."""
    essay = write_essay("cat").result()
    is_approved = interrupt(
        {
            # Any json-serializable payload provided to interrupt as argument.
            # It will be surfaced on the client side as an Interrupt when streaming data
            # from the workflow.
            "essay": essay,  # The essay we want reviewed.
            # We can add any additional information that we need.
            # For example, introduce a key called "action" with some instructions.
            "action": "Please approve/reject the essay",
        }
    )
    return {
        "essay": essay,  # The essay that was generated
        "is_approved": is_approved,  # Response from HIL
    }


thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}
for item in workflow.stream("cat", config):
    print(item)
# > {'write_essay': 'An essay about topic: cat'}
# > {
# >     '__interrupt__': (
# >        Interrupt(
# >            value={
# >                'essay': 'An essay about topic: cat',
# >                'action': 'Please approve/reject the essay'
# >            },
# >            id='b9b2b9d788f482663ced6dc755c9e981'
# >        ),
# >    )
# > }


# 论文已撰写完成，待审阅。收到审阅意见后，我们即可继续后续工作流程
from langgraph.types import Command

# Get review from a user (e.g., via a UI)
# In this case, we're using a bool, but this can be any json-serializable value.
human_review = True

for item in workflow.stream(Command(resume=human_review), config):
    print(item)