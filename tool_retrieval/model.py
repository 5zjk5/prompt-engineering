from pydantic import BaseModel
from typing import Dict, Any, Optional

from sqlalchemy import true


class InsertToolRequest(BaseModel):
    """
    新工具入库，工具格式为 json
    示例：
    {
        "tool_name": "tool1",
        "description": "这是一个工具",
        "parameters": {
            "type": "object",
            "properties": {
            "request_url": {
                "type": "string",
                "description": "指定要检索详细内容的网页URL。"
            }
            },
            "required": [
                "request_url"
            ]
        }
    }
    """
    tool_json: Dict[str, Any]
    tool_optimized: Optional[bool] = True


class DeleteToolRequest(BaseModel):
    """
    根据 tool_name 删除工具
    示例：
    {
        "tool_name": "tool1"
    }
    """
    tool_name: str


class UpdateToolRequest(BaseModel):
    """
    根据 tool_name 更新工具描述，接收 json
    示例：
    {
        "tool_name": "tool1",
        "description": "这是一个工具",
        "parameters": {
            "type": "object",
            "properties": {
            "request_url": {
                "type": "string",
                "description": "指定要检索详细内容的网页URL。"
            }
            },
            "required": [
                "request_url"
            ]
        }
    }
    """
    tool_json: Dict[str, Any]


class SelectToolRequest(BaseModel):
    """
    1、根据 tool_name 获取工具信息
    2、没有 tool_name 默认获得所有工具信息
    示例：
    {
        "tool_name": "tool1"
    }
    """
    tool_name: Optional[str] = None


class RetrievalToolRequest(BaseModel):
    """
    根据 query 检索工具
    示例：
    {
        "query": "检索工具",
        "method": "hybrid",
        "n_results": 5
    }
    """
    query: str
    method: Optional[str] = "hybrid"  # 可选值为 "dense", "sparse", "hybrid", "keyword"
    n_results: Optional[int] = 5
