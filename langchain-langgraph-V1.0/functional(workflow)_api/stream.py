from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer  # 相当于自定义中途要流式输出的内容 

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def main(inputs: dict) -> int:
    writer = get_stream_writer()   
    writer("Started processing")   
    result = inputs["x"] * 2
    writer(f"Result is {result}")   
    return result

config = {"configurable": {"thread_id": "abc"}}

for mode, chunk in main.stream(   
    {"x": 5},
    stream_mode=["custom", "updates"],   
    config=config
):
    print(f"{mode}: {chunk}")