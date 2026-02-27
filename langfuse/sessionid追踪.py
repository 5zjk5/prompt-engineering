# https://langfuse.com/docs/observability/features/sessions

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler
import os
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv as load_env

load_env()

langfuse = get_client()
handler = CallbackHandler()

# Create your LangChain components
llm = ChatOpenAI(
    model=os.getenv('model'),
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key'),
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}，10个字以内")
chain = prompt | llm

# 通过with语句设置session_id
# 所有层级都属于这个 with
# with langfuse.start_as_current_observation(as_type="span", name="langchain-call"):
#     # Propagate session_id to all observations
#     with propagate_attributes(session_id="your-session-id"):
#         # Pass handler to the chain invocation
#         response = chain.invoke(
#             {"topic": "dog"},
#             config={"callbacks": [handler]},
#         )
#         print(response.content)


# 通过 metadata 直接设置 session_id
# 单条调用
response = chain.invoke(
    {"topic": "lalala"},
    config={
        "callbacks": [handler],
        "metadata": {
            "langfuse_session_id": "your-session-id",
        }
    }
)
print(response.content)

# 刷新事件以确保数据发送到 Langfuse
langfuse.flush()


