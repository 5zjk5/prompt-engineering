# https://docs.langchain.com/oss/python/langgraph/quickstart
import operator
from langchain.tools import tool
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
from langchain.messages import SystemMessage, ToolMessage, HumanMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Azure
MODEL = "gpt-4.1"
azure_api_version='2025-03-01-preview'
azure_endpoint=""
azure_api_key=""
model = ChatOpenAIModel(
        model=MODEL,
        use_azure=True,  # 使用微软openai接口
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# 定义图状态，operator.add确保新消息追加到现有列表，而不是替换现有列表
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# 定义模型节点
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


# 定义工具节点
def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# 定义结束节点
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(  # 表示判断节点
    "llm_call",  # 表示从 llm_call 节点开始判断
    should_continue,  # 表示判断函数
    ["tool_node", END]  # 表示可去的节点
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# Show the agent
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
# 保存为 PNG 文件
graph = agent.get_graph(xray=True)  # xray=True 参数表示显示更详细的信息，包括内部节点和边的详细信息
png_data = graph.draw_mermaid_png()
# 保存到文件
with open("calculator_agent_graph.png", "wb") as f:
    f.write(png_data)

# Invoke
messages = [HumanMessage(content="Add 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
