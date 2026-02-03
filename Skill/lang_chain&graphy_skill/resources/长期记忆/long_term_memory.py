# https://docs.langchain.com/oss/python/langchain/long-term-memory#memory-storage
# LangGraph 将长期记忆以 JSON 文档的形式存储在存储库中。
# namespace每个内存都以自定义的命名空间（类似于文件夹）和唯一的命名空间（类似于文件名）进行组织key。
# 命名空间通常包含用户或组织 ID 或其他标签，以便于组织信息。
# 这种结构支持对内存进行层级组织。然后，通过内容过滤器支持跨命名空间搜索。

from langgraph.store.memory import InMemoryStore


def embed(texts: list[str]) -> list[list[float]]:
    # 将实际嵌入函数或LangChain嵌入对象替换
    return [[1.0, 2.0] * len(texts)]


# InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production use.
store = InMemoryStore(
    index={
        "embed": embed,  # langchain 的 embedding 模型对象，用于检索
        "dims": 2,  # 嵌入向量的维度。
    }
)
user_id = "my-user"
application_context = "chitchat"
namespace = (user_id, application_context) 
store.put( 
    namespace,
    "a-memory",  # key 命名空间内的唯一标识符。与命名空间一起形成项目的完整路径。
    # value 字典包含项的数据。必须包含字符串键和JSON可序列化值。
    {
        "rules": [
            "User likes short, direct language",
            "User only speaks English & python",
        ],
        "my-key": "my-value",
    },
)
# get the "memory" by ID
item = store.get(namespace, "a-memory") 
print(item)
print('=' * 20)
# search for "memories" within this namespace, filtering on content equivalence, sorted by vector similarity
items = store.search( 
    namespace,  # 需要查找的命名空间前缀。
    filter={"my-key": "my-value"},  # 键值对用于筛选结果。
    query="language preferences",  # 查询字符串，用于计算相似度。
)
print(items)
