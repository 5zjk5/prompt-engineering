# https://docs.langchain.com/oss/python/langchain/test#inmemorysaver-checkpointer
# 测试用的，包对话历史保存到内存，模拟了带历史的对话

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from ChatOpenAIModel_LangChian import ChatOpenAIModel
from langchain_core.runnables import RunnableConfig


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-flash"
extra_body = {
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 0,
            "include_thoughts": True
          }
        }
      }
    }
model = ChatOpenAIModel(
        api_key=API_KEY,
        base_url=BASE_URL,
        extra_body=extra_body,
        model=MODEL,
)

agent = create_agent(
    model,
    tools=[],
    checkpointer=InMemorySaver()  # 使用了这个，这必须有 config 传进去
)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

# First invocation
res1 = agent.invoke({"messages": "I live in Sydney, Australia."}, config)
print(res1)

# Second invocation: the first message is persisted (Sydney location), so the model returns GMT+10 time
res2 = agent.invoke({"messages": "What's my local time?"}, config)
print(res2)
