from langchain_openai import OpenAIEmbeddings


class DataEmbedding:
    """向量 model"""

    def init_embedding_model(self):
        """初始化向量化模型，使用阿里云的text-embedding-v4模型"""
        model = "text-embedding-v4"
        base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        api_key = ''

        embeddings = OpenAIEmbeddings(
            model=model,
            base_url=base_url,
            api_key=api_key,
            tiktoken_enabled=False,  # 非 openai 官方模型需设置
            check_embedding_ctx_length=False,  # 非 openai 官方模型需设置
            chunk_size=10  # 批次大小
        )
        return embeddings
