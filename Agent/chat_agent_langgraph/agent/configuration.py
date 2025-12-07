import logging
from typing import Any
from pydantic import BaseModel, Field


class Configuration(BaseModel):

    logger: Any = Field(
        default=logging.getLogger("default"),
        exclude=True  # exclude=True 跳过序列化，方便在 invoke 时传入日志
    )  

    llm: Any = Field(
        description="大模型实例对象"
    )  
