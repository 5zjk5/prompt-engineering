# https://docs.langchain.com/oss/python/langchain/middleware#llm-tool-selector
# 使用 LLM 在调用主模型之前智能地选择相关工具。
# 非常适合：
# 代理拥有许多工具（10 种以上），但大多数工具与每次查询无关。
# 通过过滤无关工具来减少令牌使用量
# 提高模型聚焦性和准确性

from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolSelectorMiddleware


agent = create_agent(
    model="openai:gpt-4o",
    tools=[tool1, tool2, tool3, tool4, tool5, ...],  # Many tools
    middleware=[
        LLMToolSelectorMiddleware(
            model="openai:gpt-4o-mini",  # Use cheaper model for selection
            max_tools=3,  # 可选择的工具最大数量。默认无限制。
            always_include=["search"],  # 选择中始终包含的工具名称列表
            system_prompt="你是一个智能助手，负责选择与用户查询相关的工具。"  # 选择模型的说明。如果未指定，则使用内置提示。
        ),
    ],
)
