# https://docs.langchain.com/oss/python/langchain/middleware#summarization
# 当接近会话次数上限时，自动汇总对话历史记录。
# 适合：
# 超出上下文窗口的长时间对话
# 多轮对话，历史悠久
# 需要保留完整对话上下文的应用程序

# 在 短期记忆/summary_message.py 有跑通的使用示例

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware


agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",  # 必选
            max_tokens_before_summary=4000,  # 默认为 None 就不开启，超过 n 个 token 就触发总结
            messages_to_keep=20,  # 默认值20，总结后，在 message 中保留最后 n 条消息，及当前 hum msg-ai msg 对
            summary_prompt="Custom prompt for summarization...",  # 如果未指定，则使用内置模板。
            # token_counter=func,  # 函数，自定义令牌计数函数。默认为基于字符的计数
            summary_prefix="## 上一次对话摘要：",   # default:"## Previous conversation summary:" 摘要消息的前缀
        ),
    ],
)
