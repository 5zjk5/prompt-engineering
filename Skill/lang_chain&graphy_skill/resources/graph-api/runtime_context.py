# 创建图时，您可以指定context_schema传递给节点的运行时上下文。这对于向节点传递不属于图状态的信息非常有用。例如，您可能需要传递模型名称或数据库连接等依赖项。

@dataclass
class ContextSchema:
    llm_provider: str = "openai"

graph = StateGraph(State, context_schema=ContextSchema)

# context然后，您可以使用该方法的参数将此上下文传递到图中invoke。
graph.invoke(inputs, context={"llm_provider": "anthropic"})

# 然后，您可以在节点或条件边中访问和使用此上下文：
from langgraph.runtime import Runtime

def node_a(state: State, runtime: Runtime[ContextSchema]):
    llm = get_llm(runtime.context.llm_provider)
    # ...
