# pip install langgraph-checkpoint-sqlite

import sqlite3
import time
from typing import TypedDict
from ChatOpenAIModel_LangChian import ChatOpenAIModel
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_openai import OpenAIEmbeddings


# Azure
MODEL = "gpt-4.1"
azure_api_version = '2025-03-01-preview'
azure_endpoint = ""
azure_api_key = ""
model = ChatOpenAIModel(
    model=MODEL,
    use_azure=True,  # 使用微软openai接口
    azure_api_key=azure_api_key,
    azure_endpoint=azure_endpoint,
    azure_api_version=azure_api_version,
)

# 数据库连接，历史消息存储，会话级别
history_conn = sqlite3.connect(
    "chat_history.db", isolation_level=None, check_same_thread=False
)  # 历史消息存储，短期会话记忆
history_saver = SqliteSaver(history_conn)

# 长期记忆存储
embeddings = OpenAIEmbeddings(
    model="text-embedding-v4",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key='',
    tiktoken_enabled=False,
    check_embedding_ctx_length=False,
)
store_conn = sqlite3.connect(
    "chat_memory.db", isolation_level=None, check_same_thread=False
)  # 长期记忆
store = SqliteStore(
    store_conn,
    index={
        "dims": 1024,
        "embed": embeddings,
        # "fields": ["value"]  # specify which fields to embed
    },
)  # 长期用户记忆，夸会话的，可以检索
store.setup()  # 初始化表结构

# langchain langgraph 保存会保存序列化数据，不能看到数据表中的明确数据，所以单独搞一张表来存储历史消息用于查看（读取记忆是用的不是这张表）
history_conn.execute(
    """
CREATE TABLE IF NOT EXISTS history_multi_turn (
    thread_id TEXT,
    user_id TEXT,
    turn_id INTEGER,
    query TEXT,
    answer TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)
# 不需要手动commit，LangGraph会管理事务


# 定义 State 类型 - 保存会话内的对话和用户信息
class AgentState(TypedDict):
    messages: list[BaseMessage]
    user_name: str | None


def chat_node(state: AgentState, config: RunnableConfig):
    """调用 LLM 并检索用户的长期记忆"""
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"].get("user_id", "default_user")

    namespace = (user_id, "memery")
    # 从 store 中检索跟当前相关的 memery
    user_memery = store.search(
        namespace,  # 需要查找的命名空间前缀。
        # filter={"my-key": "my-value"},  # 键值对用于筛选结果。
        query=user_input,  # 当前 query，用于计算相似度。
        limit=3,
    )

    # 拼接相关记忆
    if user_memery:
        user_relevant_context = "\n".join([str(item.value) for item in user_memery if item.score > 0.55])
        state["messages"][-1].content = f'{state["messages"][-1].content}\nrelevant_context:\n{user_relevant_context}'
        
    # 调用模型，传入所有历史消息
    response = model.invoke(
        state["messages"],
    )

    return {"messages": state["messages"] + [response]}


def update_memery(state: AgentState, config: RunnableConfig):
    """更新用户记忆"""
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"].get("user_id", "default_user")

    # 保存到 history_multi_turn 表
    history_conn.execute(
        """
    INSERT INTO history_multi_turn (thread_id, user_id, turn_id, query, answer)
    VALUES (?, ?, ?, ?, ?)
    """,
        (
            thread_id,
            user_id,
            len(state["messages"]) // 2,  # 每轮对话有 2 条消息（用户 + 助手）
            state["messages"][-2].content,  # 最后一条用户消息
            state["messages"][-1].content,  # 助手回复
        ),
    )
    # 不需要手动commit，LangGraph会管理事务

    # 长期记忆写入，每次相同 的 key 会覆盖原来的，要想追加，需要不同 key
    namespace = (user_id, "memery")
    store.put(
        namespace=namespace,  # 命名空间 key，相当于唯一 id
        key=str(int(time.time())),  # 每个记忆都有一个唯一的 key，这里用时间戳
        value={
            "query": state["messages"][-2].content,
            "answer": state["messages"][-1].content,
        },
    )

    return {}


# 构建图节点
builder = StateGraph(AgentState)
builder.add_node("chat", chat_node)
builder.add_node("update_memery", update_memery)

# 构建图边
builder.add_edge(START, "chat")
builder.add_edge("chat", "update_memery")
builder.add_edge("update_memery", END)

# 编译图
# checkpointer 会在数据库创建 checkpoints、writes 表用来存储序列化历史数据，短期记忆，会话级别
# store 会在数据库创建 store、store_migrations 表用来存储序列化历史数据，向量，长期记忆
graph = builder.compile(checkpointer=history_saver, store=store)

# 生成图片并保存
png_data = graph.get_graph().draw_mermaid_png()
filename = "graph.png"
with open(filename, "wb") as f:
    f.write(png_data)


##############################
# 为用户创建唯一的 thread_id，user_id
##############################
thread_id = "session-2"
user_id = "user-2"
namespace = (user_id, "memery")
config = {
    "configurable": {
        "thread_id": thread_id,  # thread_id 可以看做对话管理中的 session id(必选)
        "user_id": user_id,  # 额外元数据，用来区分不同用户的会话
    }
}


##############################
# 多轮对话
##############################
print("=" * 50)
print("多轮对话聊天机器人 (SQLite 存储)")
print("=" * 50)
print("输入 'quit' 退出对话\n")
initial_state = {"messages": [], "user_name": None}  # 第一轮：初始化状态
while True:
    # 获取用户输入
    user_input = input("User: ").strip()
    if user_input.lower() == 'quit':
        print("再见！")
        break
    if not user_input:
        continue

    # 获取当前对话历史（从 checkpointer 恢复）
    state_snapshot = graph.get_state(config)
    if state_snapshot.values:
        current_state = state_snapshot.values  # 历史消息
    else:
        current_state = initial_state.copy()  # 当前对话

    # 添加新的用户消息
    user_message = HumanMessage(content=user_input)
    current_state["messages"] = current_state.get("messages", []) + [user_message]

    # 打印 AI 的最后一条消息
    result = graph.invoke(current_state, config)
    if result["messages"]:
        last_message = result["messages"][-1]
        print(f"Assistant: {last_message.content}\n")
    else:
        print("Assistant 没有返回消息。\n")


##############################
# 查看历史消息 checkpointer
##############################
config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
state_snapshot = graph.get_state(config)
if state_snapshot.values and state_snapshot.values.get("messages"):
    print("\n" + "=" * 50)
    print(f"对话历史 ({user_id})")
    print("=" * 50)
    for i, msg in enumerate(state_snapshot.values["messages"], 1):
        role = "用户" if msg.type == "human" else "助手"
        print(f"\n[{i}] {role}: {msg.content}")
else:
    print("暂无对话历史")


##############################
# 查看长期记忆 store
##############################
namespace = (user_id, "memery")
# user_prefs = store.get(namespace, "memery")  # 获取单条指定 key 的记忆，这里 key 为 memery
user_memery = store.search(
    namespace,  # 需要查找的命名空间前缀。
    # filter={"my-key": "my-value"},  # 键值对用于筛选结果。
    # query="language preferences",  # 查询字符串，用于计算相似度。
)
print("\n" + "=" * 50)
print(f"用户记忆 ({user_id})")
print("=" * 50)
if user_memery:
    for item in user_memery:
        print(item.value)
else:
    print("暂无保存的记忆")
