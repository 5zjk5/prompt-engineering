# https://docs.langchain.com/oss/python/langchain/structured-output#custom-tool-message-content
# 该tool_message_content参数允许您自定义生成结构化输出时对话历史记录中显示的消息
# 最后输出会输出结构化的的内容，是一个 tool msg 消息，可通过 structured_response 字段获取结构化内容

from pydantic import BaseModel, Field
from typing import Literal
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
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


class MeetingAction(BaseModel):
    """Action items extracted from a meeting transcript."""
    task: str = Field(description="The specific task to be completed")
    assignee: str = Field(description="Person responsible for the task")
    priority: Literal["low", "medium", "high"] = Field(description="Priority level")


agent = create_agent(
    model=model,
    tools=[],
    response_format=ToolStrategy(
        schema=MeetingAction,
        tool_message_content="Action item captured and added to meeting notes!"  # 在作为 tool msg 的 content 内容
    )
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "From our meeting: Sarah needs to update the project timeline as soon as possible"}]
})

print(result["structured_response"])
# MeetingAction(task='update the project timeline', assignee='Sarah', priority='high')
