from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma


class EmbeddingVectorDB():

    @classmethod
    def load_local_embedding_model(cls, embedding_model_path, device):
        """加载本地向量模型"""
        embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_path, model_kwargs={'device': device})
        return embedding_model

    @classmethod
    def load_chroma_vector(cls, vector_db_path, embedding_model):
        print('加载向量数据库路径 =》', vector_db_path)
        db = Chroma(persist_directory=vector_db_path, embedding_function=embedding_model)
        return db

    @classmethod
    def create_chroma_vector(cls, split_docs, vector_db_path, embedding_model):
        print('创建向量数据库路径 =》', vector_db_path)
        db = Chroma.from_documents(split_docs, embedding_model, persist_directory=vector_db_path)
        db.persist()
        return db
