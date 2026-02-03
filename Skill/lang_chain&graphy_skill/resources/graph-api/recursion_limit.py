# 递归限制设置了图在单次执行期间可以执行的最大超级步骤数。
# 一旦达到此限制，LangGraph 将抛出异常GraphRecursionError。
# 默认情况下，此值设置为 25 步。
# 递归限制可以在运行时为任何图设置，并通过配置字典传递给 `/`。
# 重要的是，` /`是一个独立的键，不应像所有其他用户定义的配置一样，将其放在 `/` 键中传递invoke

graph.invoke(inputs, config={"recursion_limit": 5}, context={"llm": "anthropic"})

# 当前步数计数器可在config["metadata"]["langgraph_step"]任何节点内访问，从而允许在达到递归限制之前主动处理递归。这使您可以在图逻辑中实现优雅降级策略。
current_step = config["metadata"]["langgraph_step"]
recursion_limit = config["recursion_limit"]

# 当超过限制时，LangGraph 会引发GraphRecursionError.

from langgraph.errors import GraphRecursionError

try:
    graph.invoke(inputs, {"recursion_limit": 3})
except GraphRecursionError:
    print("Recursion Error")
    