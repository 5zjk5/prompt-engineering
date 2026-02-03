# https://docs.langchain.com/oss/python/langchain/structured-output#tool-calling-strategy
# 数据类：带有类型注释的 Python 数据类
# 最后输出会输出结构化的 json 内容，是一个 tool msg 消息，可通过 structured_response 字段获取结构化内容

from typing_extensions import TypedDict
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


# 如果需要每个字段注释说明，写字符串文档中，给 llm 理解的
class ProductReview(TypedDict):
    """Analysis of a product review."""
    rating: int | None  # The rating of the product (1-5)
    sentiment: Literal["positive", "negative"]  # The sentiment of the review
    key_points: list[str]  # The key points of the review


agent = create_agent(
    model=model,
    tools=[],
    response_format=ToolStrategy(ProductReview)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this review: 'Great product: 5 out of 5 stars. Fast shipping, but expensive'"}]
})
print(result["structured_response"])  
# {'rating': 5, 'sentiment': 'positive', 'key_points': ['Fast shipping', 'Great product', 'Expensive']}
