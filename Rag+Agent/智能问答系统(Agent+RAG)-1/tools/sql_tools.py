from utils.sqlite_db import execute_sql


execute_sql_tool = {
        "type": "function",
        "function": {
            "name": execute_sql,
            "description": "用于执行用户输入的 SQL 语句，并返回执行结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "description": "完整可执行的 SQL 语句",
                        "type": "string"
                    },
                },
                "required": ["sql"]
            }
        }
      }

sql_tools = [
    execute_sql_tool
]
