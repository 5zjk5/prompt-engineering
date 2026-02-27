"""
https://langfuse.com/docs/observability/features/tags
"""


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
# 要么设置环境变量，要么设置构造函数参数。后者优先。
os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = "production"  # 通过这里设置区分测试，生产等等
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

# 通过with语句设置
# 所有层级都属于这个 with
with langfuse.start_as_current_observation(as_type="span", name="langchain-call"):
    # Propagate session_id to all observations
    with propagate_attributes(tags=["tag-1", "tag-2"]):
        # Pass handler to the chain invocation
        response = chain.invoke(
            {"topic": "冰箱"},
            config={"callbacks": [handler]},
        )
        print(response.content)


# 通过 metadata 直接设置
# 单条调用
response = chain.invoke(
    {"topic": "cat小猫咪s"},
    config={
        "callbacks": [handler],
        "metadata": {
            "langfuse_tags": ["tag-1", "tag-2"]
        }
    }
)
print(response.content)

# 刷新事件以确保数据发送到 Langfuse
langfuse.flush()



