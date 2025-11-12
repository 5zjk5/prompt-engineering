from langchain.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ParentDocumentRetriever
from langchain_community.document_transformers import LongContextReorder
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.storage import InMemoryStore


class Retriever():

    @classmethod
    def similarity(cls, db, query, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/vectorstore/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        相似度，不带分数的，会把检索出所有最相似的返回，如果文档中有重复的，那会返回重复的
        :param db:
        :param query:
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_kwargs={'k': topk})
        retriever_docs = retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def similarity_with_score(cls, db, query, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/integrations/vectorstores/usearch/#similarity-search-with-score
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        带分数的，距离分数是L2距离。因此，分数越低越好
        :param db:
        :param query:
        :param long_context: 长上下文排序
        :return:
        """
        retriever_docs = db.similarity_search_with_score(query, k=topk)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def mmr(cls, db, query, topk=5, fetch_k=50, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/vectorstore/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        mmr 算法会去重，会把检索出所有最相似的返回
        :param db:
        :param query:
        :param topk: 指定最相似的返回几个， 最多返回的数量不会超过 fetch_k
        :param fetch_k: 给 mmr 的最多文档数
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_type="mmr", search_kwargs={'k': topk, 'fetch_k': fetch_k})
        retriever_docs = retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def similarity_score_threshold(cls, db, query, topk=5, score_threshold=0.8, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        相似分数过滤
        :param db:
        :param query:
        :param topk:
        :param score_threshold: 相似分数
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_type="similarity_score_threshold",
                                    search_kwargs={'k': topk, "score_threshold": score_threshold})
        retriever_docs = retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def multi_query_retriever(cls, db, query, model, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/MultiQueryRetriever/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        多查询检索器
        基于向量距离的检索可能因微小的询问词变化或向量无法准确表达语义而产生不同结果；
        使用大预言模型自动从不同角度生成多个查询，实现提示词优化；
        对用户查询生成表达其不同方面的多个新查询（也就是query利用大模型生成多个表述），对每个表述进行检索，去结果的并集；
        优点是生成的查询多角度，可以覆盖更全面的语义和信息需求；
        指定 topk 好像没用，不知道为什么
        :param db:
        :param query:
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_kwargs={'k': topk})
        retriever = MultiQueryRetriever.from_llm(retriever=retriever, llm=model)
        retriever_docs = retriever.get_relevant_documents(query=query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def contextual_compression_by_llm(cls, db, query, model, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/contextual_compression/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        上下文压缩检索器，大模型，会对结果去重
        使用给定查询的上下文来压缩检索的输出，以便只返回相关信息，而不是立即按照原样返回检索到的文档
        相当于提取每个检索结果的核心，简化每个文档，利用大模型的能力
        不知道为什么 topk 不管用
        :param db:
        :param query:
        :param model:
        :param topk:
        :param long_context: 长上下文排序
        :return:
        """
        _filter = LLMChainFilter.from_llm(model)
        retriever = db.as_retriever(search_kwargs={'k': topk})
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=_filter, base_retriever=retriever
        )
        retriever_docs = compression_retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def contextual_compression_by_embedding(cls, db, query, embedding_model, topk=5, similarity_threshold=0.76,
                                            long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/contextual_compression/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        上下文压缩检索器，embedding 模型，会对结果去重
        使用给定查询的上下文来压缩检索的输出，以便只返回相关信息，而不是立即按照原样返回检索到的文档
        利用 embedding 来计算
        :param db:
        :param query:
        :param embedding_model:
        :param topk:
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_kwargs={'k': topk})
        embeddings_filter = EmbeddingsFilter(embeddings=embedding_model, similarity_threshold=similarity_threshold)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=embeddings_filter, base_retriever=retriever
        )
        retriever_docs = compression_retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def contextual_compression_by_embedding_split(cls, db, query, embedding_model, topk=5, similarity_threshold=0.76,
                                                  chunk_size=100, chunk_overlap=0, separator=". ", long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/contextual_compression/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        上下文压缩检索器，embedding 模型，会对结果去重，将文档分割成更小的部分
        使用给定查询的上下文来压缩检索的输出，以便只返回相关信息，而不是立即按照原样返回检索到的文档
        利用 embedding 来计算
        :param db:
        :param query:
        :param embedding_model:
        :param topk: 不生效，默认是 4 个
        :param long_context: 长上下文排序
        :return:
        """
        retriever = db.as_retriever(search_kwargs={'k': topk})
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=separator)
        redundant_filter = EmbeddingsRedundantFilter(embeddings=embedding_model)
        relevant_filter = EmbeddingsFilter(embeddings=embedding_model, similarity_threshold=similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, redundant_filter, relevant_filter]
        )
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=retriever
        )
        retriever_docs = compression_retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs


    @classmethod
    def ensemble(cls, query, text_split_docs, embedding_model, bm25_topk=5, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/ensemble/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        混合检索
        最常见的模式是将稀疏检索器（如 BM25）与密集检索器（如嵌入相似性）相结合，因为它们的优势是互补的。它也被称为“混合搜索”。
        稀疏检索器擅长根据关键词查找相关文档，而密集检索器擅长根据语义相似度查找相关文档。
        :param query:
        :param text_split_docs: langchain 分割后的文档对象
        :param long_context: 长上下文排序
        :param bm25_topk: bm25 topk
        :param topk: 相似性 topk
        :return: 会返回两个的并集，结果可能会小于 bm25_topk + topk
        """
        text_split_docs = [text.page_content for text in text_split_docs]
        bm25_retriever = BM25Retriever.from_texts(
            text_split_docs, metadatas=[{"source": 1}] * len(text_split_docs)
        )
        bm25_retriever.k = bm25_topk

        faiss_vectorstore = Chroma.from_texts(
            text_split_docs, embedding_model, metadatas=[{"source": 2}] * len(text_split_docs)
        )
        faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": topk})

        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
        )
        retriever_docs = ensemble_retriever.invoke(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def bm25(cls, query, text_split_docs, topk=5, long_context=False):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        稀疏检索器擅长根据关键词查找相关文档
        :param query:
        :param text_split_docs: langchain 分割后的文档对象
        :param topk:
        :param long_context: 长上下文压缩
        """
        text_split_docs = [text.page_content for text in text_split_docs]
        bm25_retriever = BM25Retriever.from_texts(
            text_split_docs, metadatas=[{"source": 1}] * len(text_split_docs)
        )
        bm25_retriever.k = topk
        retriever_docs = bm25_retriever.get_relevant_documents(query)
        if long_context:
            reordering = LongContextReorder()
            retriever_docs = reordering.transform_documents(retriever_docs)
        return retriever_docs

    @classmethod
    def parent_document_retriever(cls, docs, query, embedding_model):
        """
        https://python.langchain.com/docs/modules/data_connection/retrievers/parent_document_retriever/
        https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder/
        父文档检索，只适合，chroma 数据库, faiss 不支持
        适合多个文档加载进来后检索出符合的小文本段，及对应大的 txt
        可以根据此方法，检索出来大的 txt 后，用其他方法再精细化检索 txt 中的内容
        :param docs: example
            loaders = [
                        TextLoader("data/专业描述.txt", encoding="utf-8"),
                        TextLoader("data/专业描述_copy.txt", encoding="utf-8"),
                    ]
            docs = []
            for loader in loaders:
                docs.extend(loader.load())
        :return:
        """
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)
        vectorstore = Chroma(
            collection_name="full_documents", embedding_function=embedding_model
        )
        store = InMemoryStore()
        retriever = ParentDocumentRetriever(
            vectorstore=vectorstore,
            docstore=store,
            child_splitter=child_splitter,
        )

        retriever.add_documents(docs, ids=None)
        sub_docs = vectorstore.similarity_search(query)
        parent_docs = retriever.get_relevant_documents(query)

        return sub_docs, parent_docs
