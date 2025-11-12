import os
import faiss
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS


class EmbeddingVector():

    def to_vector(self, split_docs, embedding_model):
        """将文档转换为向量"""
        split_docs = split_docs[:5]
        vector_path = './vector'

        # 内存中存储向量
        memory_store = InMemoryVectorStore(embedding=embedding_model)
        memory_store.add_documents(documents=split_docs)  # 通用方法

        # chroma 数据库
        # https://docs.langchain.com/oss/python/integrations/vectorstores/chroma
        chroma_path = os.path.join(vector_path, "chroma_langchain_db")
        if not os.path.exists(chroma_path):
            print(f'创建 chroma 数据库: {chroma_path}')
            chrome_store = Chroma(
                collection_name="example_collection",
                embedding_function=embedding_model,
                persist_directory=chroma_path
            )
            chrome_store.add_documents(documents=split_docs)
        else:
            print(f'加载 chroma 数据库: {chroma_path}')
            chrome_store = Chroma().from_documents(
                collection_name='example_collection',
                documents=split_docs,
                embedding=embedding_model,
                persist_directory=chroma_path
            )

        # faiss
        # https://docs.langchain.com/oss/python/integrations/vectorstores/faiss#saving-and-loading
        faiss_path = os.path.join(vector_path, "faiss_langchain_db")
        if not os.path.exists(faiss_path):
            print(f'创建 faiss 数据库: {faiss_path}')
            embedding_dim = len(embedding_model.embed_query("hello world"))
            index = faiss.IndexFlatL2(embedding_dim)
            faiss_store = FAISS(
                embedding_function=embedding_model,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            ).from_documents(documents=split_docs, embedding=embedding_model)
            faiss_store.save_local(faiss_path)
        else:
            print(f'加载 faiss 数据库: {faiss_path}')
            faiss_store = FAISS.load_local(
                faiss_path,
                embedding_model,
                allow_dangerous_deserialization=True,
            )

        return memory_store, chrome_store, faiss_store
