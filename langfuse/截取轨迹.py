import os
import re
import json
from datetime import datetime
from typing import Annotated
from dotenv import load_dotenv as load_env
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

load_env()


# ==================== 步骤 1: 定义工具 ====================
@tool
def get_user_info(user_id: str) -> dict:
    """
    获取用户信息（包含敏感数据）

    Args:
        user_id: 用户ID

    Returns:
        包含用户信息的字典
    """
    return {
        "user_id": user_id,
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "138-1234-5678",
        "credit_card": "6222 0888 8888 8888",
    }


# ==================== 步骤 2: 定义 Masking 函数 ====================
def comprehensive_masking_function(data, **kwargs):
    """
    组合功能：
    1. 保存所有原始轨迹数据（包括输入、工具调用、参数、输出）
    2. 去除敏感信息（邮箱、电话、信用卡等）
    """
    # 过滤掉 None 和空数据
    if data is None or (isinstance(data, str) and not data.strip()):
        return data

    # 功能 1: 保存原始轨迹数据
    try:
        with open("traces_original.log", "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "data_type": str(type(data).__name__),
                "data": str(data),
                "context": {k: str(v)[:200] for k, v in kwargs.items()},
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"保存原始数据失败: {e}")

    # 功能 2: 递归去除敏感信息
    def mask_sensitive_data(obj):
        if isinstance(obj, str):
            obj = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[REDACTED_EMAIL]', obj)
            obj = re.sub(r'\b\d{3}[-.\s]?\d{4}[-.\s]?\d{4}\b', '[REDACTED_PHONE]', obj)
            obj = re.sub(r'\b\d{11}\b', '[REDACTED_PHONE]', obj)
            obj = re.sub(
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CC]', obj
            )
            obj = re.sub(r'\b\d{17}[\dXx]\b', '[REDACTED_ID]', obj)
            return obj
        elif isinstance(obj, dict):
            return {k: mask_sensitive_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [mask_sensitive_data(item) for item in obj]
        else:
            return obj

    masked_data = mask_sensitive_data(data)

    return masked_data


# ==================== 步骤 3: 初始化 Langfuse ====================
# 只初始化一次,带masking功能
langfuse = Langfuse(mask=comprehensive_masking_function)
handler = CallbackHandler()

# ==================== 步骤 4: 创建 LangGraph Agent ====================
llm = ChatOpenAI(
    model=os.getenv('model'),
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key'),
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)


# 定义 Agent 状态
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 创建工具绑定
tools = [get_user_info]
llm_with_tools = llm.bind_tools(tools)


# 定义 Agent 节点
def agent_node(state: AgentState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 定义工具执行节点
def tool_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]

    tool_outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_func = None
        for t in tools:
            if t.name == tool_name:
                tool_func = t
                break

        if tool_func:
            result = tool_func.invoke(tool_args)
            tool_outputs.append(
                ToolMessage(
                    content=str(result), tool_call_id=tool_call["id"], name=tool_name
                )
            )

    return {"messages": tool_outputs}


# 定义路由函数
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    return END


# 构建图
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)
graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", should_continue)
graph_builder.add_edge("tools", "agent")

# 编译图
agent_graph = graph_builder.compile()

# ==================== 步骤 5: 执行调用 ====================
print("=" * 60)
print("开始执行 LangGraph Agent 调用（自动执行工具）")
print("=" * 60)

try:
    # 使用 LangGraph 的 stream 方式执行
    final_state = None
    for event in agent_graph.stream(
        {
            "messages": [
                HumanMessage(
                    content="你是一个客服助手。当用户询问账户信息时,使用 get_user_info 工具获取信息。请帮我查询用户ID为 user_12345 的账户信息"
                )
            ]
        },
        config={
            "callbacks": [handler],
            "metadata": {
                "langfuse_session_id": "session_001",
                "langfuse_user_id": "user_12345",
            },
        },
    ):
        print(f"Event: {event}")
        final_state = event

    print("\n" + "=" * 60)
    print("Agent 最终响应:")
    print("=" * 60)
    if final_state:
        for node_name, node_state in final_state.items():
            messages = node_state.get("messages", [])
            for msg in messages:
                if isinstance(msg, AIMessage) and not msg.tool_calls:
                    print(msg.content)
except Exception as e:
    print(f"执行失败: {e}")

# ==================== 步骤 6: 刷新数据 ====================
print("\n" + "=" * 60)
print("刷新数据到 Langfuse...")
print("=" * 60)
langfuse.flush()

print("\n✅ 完成！请检查以下文件:")
print("  - traces_original.log (原始轨迹，包含敏感信息)")
print("  - Langfuse UI (仅包含屏蔽后的数据)")
