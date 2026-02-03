# https://docs.langchain.com/oss/python/langchain/middleware#planning
# 为复杂的多步骤任务添加待办事项列表管理功能。
# 该中间件会自动为代理提​​供write_todos工具和系统提示，以指导有效的任务规划。
# 相当于这个中间件是一个工具


from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import HumanMessage


agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[TodoListMiddleware(
        system_prompt="",  # 自定义系统提示，用于指导待办事项的使用。如果未指定，则使用内置提示。
        tool_description=""  # 工具的自定义描述write_todos。如果未指定，则使用内置描述。
    )],
)

result = agent.invoke({"messages": [HumanMessage("Help me refactor my codebase")]})
print(result["todos"])  # Array of todo items with status tracking
