# https://docs.langchain.com/oss/python/langchain/middleware#context-editing
# 通过精简、总结或清除工具使用情况来管理对话上下文。
# 非常适合：
# 需要定期清理上下文的长篇对话
# 从上下文中移除失败的工具尝试
# 自定义上下文管理策略

from langchain.agents import create_agent
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit


agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[
        ContextEditingMiddleware(
            edits=[
                ClearToolUsesEdit(
                    trigger=1000,  # 触发编辑的令牌计数阈值
                    clear_at_least=0,  # 回收的最小代币数，保留多少 token
                    keep=3,  # 要保存的最近工具结果的数量
                    clear_tool_inputs=False,  # 是否清除工具调用参数
                    exclude_tools=(),  # 排除在清除范围之外的工具名称列表
                    placeholder="[cleared]"  # 清除输出的占位符文本
                ),  
            ],
            token_count_method="approximate",  # default "approximate"  令牌计数方法。选项："approximate"或"model"
        ),
    ],
)
