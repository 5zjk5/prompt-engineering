# https://docs.langchain.com/oss/python/langchain/structured-output#error-handling
# 如果错误会自己纠正调整的，详细见文档，类型错误，取值错误

from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field, Union
from typing import Literal


class MeetingAction(BaseModel):
    """Action items extracted from a meeting transcript."""
    task: str = Field(description="The specific task to be completed")
    assignee: str = Field(description="Person responsible for the task")
    priority: Literal["low", "medium", "high"] = Field(description="Priority level")


# 关闭错误处理，默认 true
response_format = ToolStrategy(
    schema=MeetingAction,
    handle_errors=False  # All errors raised
)

# 自定义错误信息 如果handle_errors是字符串，代理将始终使用固定工具消息提示模型重试
ToolStrategy(
    schema=MeetingAction,
    handle_errors="Please provide a valid rating between 1-5 and include a comment."
)

# 仅处理特定异常 如果handle_errors是异常类型，则仅当引发的异常属于指定类型时，代理才会重试（使用默认错误消息）
ToolStrategy(
    schema=MeetingAction,
    handle_errors=ValueError  # Only retry on ValueError, raise others， 处理这两种异常 (ValueError, TypeError)
)

# 自定义错误处理函数
from langchain.agents.structured_output import StructuredOutputValidationError, MultipleStructuredOutputsError

def custom_error_handler(error: Exception) -> str:
    if isinstance(error, StructuredOutputValidationError):
        return "There was an issue with the format. Try again."
    elif isinstance(error, MultipleStructuredOutputsError):
        return "Multiple structured outputs were returned. Pick the most relevant one."
    else:
        return f"Error: {str(error)}"

ToolStrategy(
    schema=Union[MeetingAction],
    handle_errors=custom_error_handler
)
