# openai 接口的 embedding 模型，支持那些可以用 opanai 兼容的模型

from langchain_openai import OpenAIEmbeddings

# modelscope
model="Qwen/Qwen3-Embedding-8B"
base_url='https://api-inference.modelscope.cn/v1'
api_key=''

# aliyun
model="text-embedding-v4"
base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
api_key=''


embeddings = OpenAIEmbeddings(
    model=model,
    base_url=base_url,
    api_key=api_key,
    tiktoken_enabled=False,
    check_embedding_ctx_length=False,
)

# 单个
input_text = "The meaning of life is 42"
vector = embeddings.embed_query("hello")
print(vector[:3])

# 多个
vectors = embeddings.embed_documents(["hello", "goodbye"])
print(len(vectors))
print(vectors[0][:3])
