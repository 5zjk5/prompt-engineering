# https://docs.langchain.com/oss/python/langchain/test#without-reference-trajectory
# 使用 LLM 通过该函数评估智能体的执行路径create_trajectory_llm_as_judge。与轨迹匹配评估器不同，它不需要参考轨迹，但如果存在参考轨迹，也可以提供。
# 写提示词评判，更灵活简便，根据场景自定义提示词，评估智能体的执行路径是否符合预期。

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT, TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-flash"
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


agent = create_agent(model, tools=[get_weather])

evaluator = create_trajectory_llm_as_judge(  
    judge=model,  
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,  # 提示词可以自定义，必须传入 outputs，reference_outputs
)  


def test_trajectory_quality():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Seattle?")]
    })

    # 设定参考轨迹
    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}}
        ]),
        ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"),
        AIMessage(content="The weather in San Francisco is 75 degrees and sunny."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],  # 必选输出 messages
        reference_outputs=reference_trajectory,  # 参考轨迹
    )
    # {
    #     'key': 'trajectory_accuracy',
    #     'score': True,
    #     'comment': 'The provided agent trajectory is reasonable...'  # 理由
    # }
    assert evaluation["score"] is True


test_trajectory_quality()
