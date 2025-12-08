from agent.state import AgentInputState, AgentState
from agent.configuration import Configuration
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.config import get_stream_writer
from langchain_core.messages import AIMessage
from agent.memery import Memory


async def chat(state: AgentState, config: RunnableConfig, runtime: Runtime):
    "调用大模型生成回复"
    llm = runtime.context.llm
    logger = runtime.context.logger
    logger.info("调用大模型生成回复")

    # 获取流写入器
    writer = get_stream_writer()
    
    full_response = ""
    
    # 使用 astream 逐 token 获取 LLM 输出
    async for chunk in llm.astream(state['messages']):
        token = chunk.content
        full_response += token
        # 实时发送每个 token 到客户端
        writer({"token": token})
    
    return {"messages": state["messages"] + [AIMessage(content=full_response)]}


def create_agent_graph():
    agent_graph = StateGraph(
        state_schema=AgentState,  # 定义状态类型，包含所有研究相关的信息，即中间过程信息存储
        input_schema=AgentInputState,  # 设置输入接收的数据类型，接受那些字段，会自动校验输入是否符合定义
        context_schema=Configuration,  # 配置，RunnableConfig 包含模型设置和偏好的运行时上下文配置，也就是传入运行时定义的字段内容，日志等
    )

    # 定义节点
    agent_graph.add_node("chat", chat)

    # 定义边
    agent_graph.add_edge(START, "chat")
    agent_graph.add_edge("chat", END)

    # 编译
    agent_graph = agent_graph.compile(store=Memory().store)

    # 可视化图，需要 vpn
    png_data = agent_graph.get_graph(xray=True).draw_mermaid_png()
    filename = "./agent_graph.png"
    with open(filename, "wb") as f:
        f.write(png_data)

    return agent_graph
