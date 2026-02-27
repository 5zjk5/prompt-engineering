"""
https://langfuse.com/docs/observability/features/masking
"""

import re
from langfuse import Langfuse, observe, get_client
from dotenv import load_dotenv as load_env

load_env()

# 定义屏蔽函数
def masking_function(data, **kwargs):
    if isinstance(data, str):
        # 匹配信用卡号的正则表达式
        pattern = r'\b(?:\d[ -]*?){13,19}\b'
        data = re.sub(pattern, '[REDACTED CREDIT CARD]', data)
    return data

# 使用屏蔽函数配置 Langfuse
langfuse = Langfuse(mask=masking_function)

# 获取客户端
langfuse = get_client()

# 创建包含敏感数据的示例函数
@observe()
def process_payment():
    # 包含信用卡号的模拟敏感数据
    transaction_info = "Customer paid with card number 4111 1111 1111 1111."
    return transaction_info

# 观察追踪
result = process_payment()

print(result)
# 输出：Customer paid with card number 4111 1111 1111 1111.
# （这是你的应用中的原始数据）

# 在 Langfuse UI 中，你会看到：
# Customer paid with card number [REDACTED CREDIT CARD].

# 刷新事件以确保数据发送到 Langfuse
langfuse.flush()