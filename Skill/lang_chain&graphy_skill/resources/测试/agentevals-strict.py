# https://docs.langchain.com/oss/python/langchain/test#strict-match
# 该strict模式确保轨迹中包含相同顺序且工具调用相同的消息，但允许消息内容存在差异。当您需要强制执行特定的操作顺序时，例如在授权操作之前要求进行策略查找，此功能非常有用。

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator
from ChatOpenAIModel_LangChian import ChatOpenAIModel


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


@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."


agent = create_agent(model=model, tools=[get_weather])

# 设定严格评估轨迹对象
evaluator = create_trajectory_match_evaluator(  
    trajectory_match_mode="strict",  
)  


def test_weather_tool_called_strict():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in San Francisco?")]
    })

    # 设定参考轨迹，正确
    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}}
        ]),
        ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"),
        AIMessage(content="The weather in San Francisco is 75 degrees and sunny."),
    ]

    # 执行并判断结果
    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
    # {
    #     'key': 'trajectory_strict_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True

    # 设定参考轨迹，错误
    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="The weather sunny."),
    ]

    # 执行并判断结果
    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
    # {
    #     'key': 'trajectory_strict_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True


test_weather_tool_called_strict()

