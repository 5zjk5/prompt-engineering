# 在许多使用场景中，您可能希望节点具有自定义重试策略，例如，如果您正在调用 API、查询数据库或调用 LLM 等。LangGraph 允许您向节点添加重试策略。
# 要配置重试策略，请将retry_policy参数传递给 `.` add_node。该retry_policy参数接受一个RetryPolicy命名元组对象。
# 下面我们RetryPolicy使用默认参数实例化一个对象，并将其与一个节点关联：

from langgraph.types import RetryPolicy

builder.add_node(
    "node_name",
    node_function,
    retry_policy=RetryPolicy(),
)

builder.add_node("model", call_model, retry_policy=RetryPolicy(max_attempts=5))  # 最大重试次数，包括第一次
builder.add_node(
    "query_database",
    query_database,
    retry_policy=RetryPolicy(retry_on=sqlite3.OperationalError),  # retry_on 重试出发错误类型
)

# 默认情况下，该retry_on参数使用一个default_retry_on函数，该函数会对除以下情况之外的任何异常进行重试：
# ValueError
# TypeError
# ArithmeticError
# ImportError
# LookupError
# NameError
# SyntaxError
# RuntimeError
# ReferenceError
# StopIteration
# StopAsyncIteration
# OSError
# 此外，对于流行的 http 请求库（例如）的例外情况requests，httpx它只会在收到 5xx 状态码时才重试。
