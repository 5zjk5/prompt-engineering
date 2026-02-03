# https://docs.langchain.com/oss/python/langchain/tools

from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Literal


# 1
# 使用@tool装饰器。默认情况下，函数的文档字符串会成为工具的描述
# 类型提示是必需的，因为它们定义了工具的输入架构
@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"


# 2
# 默认情况下，工具名称来自函数名称 calc，需要更具描述性的名称需要指定 calculator
# description 覆盖工具描述以获得更清晰的模型指导
@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))


# 3
# Pydantic 模型 字符串为工具描述，args_schema 为工具输入架构
class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str = Field(description="City name or coordinates")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit preference"
    )
    include_forecast: bool = Field(
        default=False,
        description="Include 5-day forecast"
    )

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp} degrees {units[0].upper()}"
    if include_forecast:
        result += "\nNext 5 days: Sunny"
    return result
