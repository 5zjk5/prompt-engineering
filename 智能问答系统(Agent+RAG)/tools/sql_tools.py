# coding:utf8
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from utils.sqlite_db import execute_sql


class SQL(BaseModel):
    sql: str = Field(description="""需要执行的 sql 语句。""")


execute_sql_tool = StructuredTool.from_function(
    func=execute_sql,
    name="execute_sql",
    args_schema=SQL,
    description="""Executes SQL queries and returns the result"""
)

sql_tools = [
    execute_sql_tool
]
