# https://docs.langchain.com/oss/python/langchain/middleware#pii-detection
# 检测和处理对话中的个人身份信息。
# 非常适合：
# 医疗保健和金融应用需符合合规要求
# 需要清理日志的客服人员
# 任何处理敏感用户数据的应用程序

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware


agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[
        # Redact emails in user input
        PIIMiddleware(
            "email",  # 要检测的个人身份信息 (PII) 类型。可以是内置类型(email, credit_card, ip, mac_address, url) ，也可以是自定义类型名称。

            # "block"- 检测到异常时抛出异常
            # "redact"- 替换为[REDACTED_TYPE]
            # "mask"- 部分遮盖（例如，****-****-****-1234）
            # "hash"- 替换为确定性哈希
            strategy="redact",  # default:"redact"
            apply_to_input=True,  # default:"True"  在模型调用之前检查用户消息
            apply_to_output=False,  # default:"False" 模型调用后检查 AI 消息
            apply_to_tool_results=False  # default:"False"  执行后检查工具结果消息
        ),
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True
        ),
        # Custom PII type with regex
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",  # 自定义检测器函数或正则表达式模式。如果未提供，则使用内置的 PII 类型检测器。
            strategy="block",  
        ),
    ],
)
