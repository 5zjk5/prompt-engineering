"""
https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing

分布式追踪

Trace ID 的特性：

Trace ID 在项目内必须是唯一的1
如果使用相同的 trace ID，所有操作会聚合到同一个 trace 中1
每次用户调用应该使用不同的 trace ID，这样才会产生多条独立的记录

如果你想区分不同的智能体或用户：

应该使用 user_id 和 session_id 等属性，而不是重复使用相同的 trace ID
"""
from langfuse import get_client, Langfuse
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv as load_env
import os

load_env()

langfuse = get_client()

external_request_id = "req_12345"
predefined_trace_id = Langfuse.create_trace_id(seed=external_request_id)

langfuse_handler = CallbackHandler()

llm = ChatOpenAI(
    model=os.getenv('model'),
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key'),
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}，10个字以内")
chain = prompt | llm

with langfuse.start_as_current_observation(
    as_type="span",
    name="langchain-request",
    trace_context={"trace_id": predefined_trace_id}
) as span:
    span.update_trace(
        input={"topic": "哈哈"}
    )
    
    response = chain.invoke(
        {"topic": "哈哈"},
        config={"callbacks": [langfuse_handler]}
    )
    
    span.update_trace(output={"response": response})

print(f"Trace ID: {predefined_trace_id}")
print(f"Trace ID: {langfuse_handler.last_trace_id}")

# 刷新事件以确保数据发送到 Langfuse
langfuse.flush()