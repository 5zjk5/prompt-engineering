# https://docs.langchain.com/oss/python/langchain/structured-output#tool-calling-strategy
# 最后输出会输出结构化的的内容，是一个 tool msg 消息，可通过 structured_response 字段获取结构化内容
# 会自动选择合适的那个

from pydantic import BaseModel, Field
from typing import Literal, Union
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
class ProductReview(BaseModel):
    """Analysis of a product review."""
    rating: int | None = Field(description="The rating of the product", ge=1, le=5)
    sentiment: Literal["positive", "negative"] = Field(description="The sentiment of the review")
    key_points: list[str] = Field(description="The key points of the review. Lowercase, 1-3 words each.")


# 如果需要每个字段注释说明，写字符串文档中，给 llm 理解的
class CustomerComplaint(BaseModel):
    """A customer complaint about a product or service."""
    issue_type: Literal["product", "service", "shipping", "billing"] = Field(description="The type of issue")
    severity: Literal["low", "medium", "high"] = Field(description="The severity of the complaint")
    description: str = Field(description="Brief description of the complaint")


agent = create_agent(
    model=model,
    tools=[],
    response_format=ToolStrategy(schema=Union[ProductReview, CustomerComplaint])
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this review: 'Great product: 5 out of 5 stars. Fast shipping, but expensive'"}]
})
print(result["structured_response"])  
# ProductReview(rating=5, sentiment='positive', key_points=['fast shipping', 'expensive'])
