import time
import threading
from agent.state import AgentInputState, AgentState
from agent.configuration import Configuration
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.config import get_stream_writer
from langchain_core.messages import AIMessage
from agent.memery import Memory


# 实例化 store
store = Memory().store


async def memery_search(state: AgentState, config: RunnableConfig, runtime: Runtime):
    "从记忆中搜索相关信息"
    user_id = runtime.context.user_id
    logger = runtime.context.logger
    logger.info("从记忆中搜索相关信息.....")

    # 从 store 中检索跟当前相关的 memery
    namespace = (user_id, "memery")
    input_query = state["messages"][-1].content
    if isinstance(input_query, list):
        for i in input_query:
            if i['type'] == 'text':
                input_query = i['text']
                break
    else:
        input_query = input_query.strip()
    related_memery = store.search(
        namespace,  # 需要查找的命名空间前缀。
        # filter={"my-key": "my-value"},  # 键值对用于筛选结果。
        query=input_query,  # 当前 query，用于计算相似度。
        limit=3,
    )
    logger.info(f'检索到相关记忆 {len(related_memery)} 条... {related_memery}')

    # 拼接相关记忆
    if related_memery:
        user_relevant_context = "\n".join(
            [str(item.value) for item in related_memery if item.score > 0.6]
        )
        state["messages"][-1].content = f'{state["messages"][-1].content}\nrelevant_context:\n{user_relevant_context}'

    return {"messages": state["messages"]}


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


def _process_memery_summary(llm, user_id, logger, messages):
    """后台处理记忆总结和写入"""
    try:
        # 总结记忆
        summary_prompt = """
        请总结以下记忆，提取出主要的信息和趋势：
        {memery}
        """
        history = []
        for his in messages:
            if his.type == 'human':
                history.append(f'用户: {his.content}')
            elif his.type == 'ai':
                history.append(f'助手: {his.content}')
        summary = llm.invoke(summary_prompt.format(memery='\n'.join(history)))
        summary = summary.content
        logger.info(f"总结记忆: {summary}")

        # 长期记忆写入，每次相同 的 key 会覆盖原来的，要想追加，需要不同 key
        namespace = (user_id, "memery")
        store.put(
            namespace=namespace,  # 命名空间 key，相当于唯一 id
            key=str(int(time.time())),  # 每个记忆都有一个唯一的 key，这里用时间戳
            value={"summary": summary},
        )
    except Exception as e:
        logger.error(f"后台记忆处理出错: {e}")


async def memery_add(state: AgentState, config: RunnableConfig, runtime: Runtime):
    "将回复添加到记忆中"
    llm = runtime.context.llm
    user_id = runtime.context.user_id
    logger = runtime.context.logger
    logger.info("长期记忆添加中....")

    messages = state["messages"]
    if len(messages) % 5 == 0:  # 每 5 轮总结一次写入长期记忆
        logger.info(f"长期记忆达到 5 的倍数，开始启动后台线程总结写入长期记忆，messags 长度 {len(messages)}")

        # 启动后台线程执行总结和写入
        thread = threading.Thread(
            target=_process_memery_summary, args=(llm, user_id, logger, messages)
        )
        thread.daemon = True  # 设置为守护线程，防止阻塞主程序退出（如果需要）
        thread.start()
    else:
        logger.info(f"长期记忆未达到 5 的倍数，不写入长期记忆，messags 长度 {len(messages)}")

    return {}


def create_agent_graph():
    agent_graph = StateGraph(
        state_schema=AgentState,  # 定义状态类型，包含所有研究相关的信息，即中间过程信息存储
        input_schema=AgentInputState,  # 设置输入接收的数据类型，接受那些字段，会自动校验输入是否符合定义
        context_schema=Configuration,  # 配置，RunnableConfig 包含模型设置和偏好的运行时上下文配置，也就是传入运行时定义的字段内容，日志等
    )

    # 定义节点
    agent_graph.add_node("memery_search", memery_search)
    agent_graph.add_node("chat", chat)
    agent_graph.add_node("memery_add", memery_add)

    # 定义边
    agent_graph.add_edge(START, "memery_search")
    agent_graph.add_edge("memery_search", "chat")
    agent_graph.add_edge("chat", "memery_add")
    agent_graph.add_edge("memery_add", END)

    # 编译
    agent_graph = agent_graph.compile(store=Memory().store)

    # 可视化图，需要 vpn
    png_data = agent_graph.get_graph(xray=True).draw_mermaid_png()
    filename = "./agent_graph.png"
    with open(filename, "wb") as f:
        f.write(png_data)

    return agent_graph
