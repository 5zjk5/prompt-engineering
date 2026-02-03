# https://docs.langchain.com/oss/python/langchain/test#unordered-match
# 该unordered模式允许以任意顺序调用相同的工具，这在您想要验证是否已检索到特定信息但并不关心检索顺序时非常有用。
# 例如，代理可能需要同时检查某个城市的天气和事件，但顺序无关紧要。

# https://docs.langchain.com/oss/python/langchain/test#subset-and-superset-match
# “superset和subset”模式匹配部分轨迹。
# “superset模式”验证智能体是否至少调用了参考轨迹中的工具，并允许调用其他工具。
# “模式subset”确保智能体没有调用参考轨迹之外的任何工具。

###### 以上两种不起作用！！！！！！！！

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-pro"
extra_body = {
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 512,
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


@tool
def get_events(city: str):
    """Get events happening in a city."""
    return f"Concert at the park in {city} tonight."


@tool
def get_name():
    """Get the name of the person."""
    return f"The name is xxxxx."


agent = create_agent(model=model, tools=[get_weather, get_events])

# 实例化评估对象，无序
evaluator = create_trajectory_match_evaluator(  
    trajectory_match_mode="subset",  
)  


def test_multiple_tools_any_order():
    result = agent.invoke({
        "messages": [HumanMessage(content="1、调用get_name获得名字。2、调用get_weather获得北京天气。3、调用get_events获得北京事件。")]
    })

    # Reference shows tools called in different order than actual execution
    reference_trajectory = [
        HumanMessage(content="What's happening in SF today?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_events", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="Concert at the park in SF tonight.", tool_call_id="call_1"),
        AIMessage(content="", tool_calls=[
            {"id": "call_2", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_2"),
        AIMessage(content="Today in SF: 75 degrees and sunny with a concert at the park tonight."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_unordered_match',
    #     'score': True,
    # }
    assert evaluation["score"] is True


test_multiple_tools_any_order()
