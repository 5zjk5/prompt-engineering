# https://docs.langchain.com/oss/python/langchain/short-term-memory#summarize-messages
# 汇总消息历史记录,要汇总代理中的消息历史记录，请使用内置的SummarizationMiddleware

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-flash"
extra_body={
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


checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model=model,
            max_tokens_before_summary=40,  # Trigger summarization at 4000 tokens
            messages_to_keep=0,  # Keep last n messages after summary，这个会最后保留一对当前对话的 hum，ai message 消息，
                                 # 如果为 1 只会有总结后 hum + 当前对话 hum， ai msg
                                 # 如果为 0 则只保留总结后的 hum + 使用此 summary 响应后的 ai msg
        )
    ],
    checkpointer=checkpointer,
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}
res1 = agent.invoke({"messages": "hi, my name is bob"}, config)
res2 = agent.invoke({"messages": "write a short poem about cats"}, config)
res3 = agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
pass
