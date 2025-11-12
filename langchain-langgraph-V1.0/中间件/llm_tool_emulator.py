# https://docs.langchain.com/oss/python/langchain/middleware#llm-tool-emulator
# 使用 LLM 模拟工具执行以进行测试，用 AI 生成的响应替换实际的工具调用。
# 非常适合：
# 无需执行真实工具即可测试代理行为
# 当外部工具不可用或昂贵时开发代理
# 在实施实际工具之前，先设计代理工作流程的原型

from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolEmulator


agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_weather, search_database, send_email],
    middleware=[
        # Emulate all tools by default
        LLMToolEmulator(),

        # Or emulate specific tools
        # 要模拟的工具名称（字符串）或 BaseTool 实例的列表。如果None为空（默认），则将模拟所有工具。如果为空，则不会模拟任何工具。
        # LLMToolEmulator(tools=["get_weather", "search_database"]),

        # Or use a custom model for emulation
        # 用于模拟工具调用的 LLM 模型。如果未指定，则使用默认模型。
        # LLMToolEmulator(model="anthropic:claude-3-5-sonnet-latest"),
    ],
)