

class DataRetrieval:
    def __init__(self, embedding_model, memory_store, chrome_store, faiss_store):
        self.embedding_model = embedding_model
        self.memory_store = memory_store
        self.chrome_store = chrome_store
        self.faiss_store = faiss_store

    def retrieval(self, query):
        """检索"""
        self.similarity_search_(query)
        self.similarity_search_score(query)
        self.search_with_mmr(query)

    def similarity_search_(self, query, topk=4):
        """相似度检索"""
        result1 = self.memory_store.similarity_search(query, k=topk)
        print(f'memory 相似检索：{result1[:1]}')

        result2 = self.chrome_store.similarity_search(query, k=topk)
        print(f'chrome 相似检索：{result2[:1]}')

        # filter 指定 source 取值为 ./data\\demo.csv 的过滤掉
        result3 = self.faiss_store.similarity_search(query, k=topk, filter={"source": r"./data\\demo.csv"})
        print(f'faiss 相似检索：{result3[:1]}')

    def similarity_search_score(self, query, topk=4):
        """相似度检索，带分数"""
        result1 = self.memory_store.similarity_search_with_score(query, k=topk)
        print(f'memory 相似检索 带分数：{result1[:1]}')

        result2 = self.chrome_store.similarity_search_with_score(query, k=topk)
        print(f'chrome 相似检索 带分数：{result2[:1]}')

        # filter 指定 source 取值为 ./data\\demo.csv 的过滤掉
        result3 = self.faiss_store.similarity_search_with_score(query, k=topk, filter={"source": r"./data\\demo.csv"})
        print(f'faiss 相似检索 带分数：{result3[:1]}')

    def search_with_mmr(self, query, topk=4):
        """返回与查询最相似的文档，包括评分和 ID。"""
        # fetch_k 要获取并传递给 MMR 算法的文档数量。
        result1 = self.memory_store.max_marginal_relevance_search(query, k=topk, fetch_k=20)
        print(f'memory mmr：{result1[:1]}')

        # lambda_mult 介于 0 和 1 之间的数字，用于确定结果之间的多样性程度，其中 0 表示最大多样性，1 表示最小多样性。
        result2 = self.chrome_store.max_marginal_relevance_search(query, k=topk, lambda_mult=1)
        print(f'chrome mmr：{result2[:1]}')

        # filter 指定 source 取值为 ./data\\demo.csv 的过滤掉
        result3 = self.faiss_store.max_marginal_relevance_search(query, k=topk, fetch_k=20, filter={"source": r"./data\\demo.csv"})
        print(f'faiss mmr：{result3[:1]}')

    # 其他
    # langchain V1.0 版本对于 rag 支持砍了好多，检索方法没了很多
    # 以上是最常用，最有效的方法
