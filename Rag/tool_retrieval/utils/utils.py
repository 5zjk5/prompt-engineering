import re
import json
from fastapi import HTTPException


def verify_tool(tool_json, logger):
    """
    验证工具 JSON 是否符合要求
    """
    required_fields = ["name", "description", "parameters"]
    for field in required_fields:
        if field == 'name' and not tool_json.get(field):
            logger.error(f"Tool name cannot be empty")
            raise HTTPException(status_code=400, detail=f"Tool name cannot be empty")
        if field not in tool_json:
            logger.error(f"Missing required field: {field}")
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")


def parse_json(json_str: str):
    """
    解析 JSON 字符串，返回字典格式
    """
    json_match = re.findall(r'```json(.*?)```', json_str, re.S)
    if json_match:
        return json.loads(json_match[0].strip())
    else:
        return 
