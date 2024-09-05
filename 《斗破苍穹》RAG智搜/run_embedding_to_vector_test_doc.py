from rag.load_data import DocsLoader
from rag.embedding_db import EmbeddingVectorDB
from rag.doc_split import TextSpliter
import time


# 按照多少字分割，允许重叠多少字
chunk_size = 1000
chunk_overlap = 20

# 本地调
embedding_model_path = r'D:\Python_project\NLP\model\bge-small-zh-v1.5'
device = 'cpu'
data_path = 'data/test_doc'
vector_db_path = f'data/test_doc_vector/test_doc_vector_{chunk_size}_metadata'


if __name__ == '__main__':
    # 向量模型加载
    embedding_model = EmbeddingVectorDB.load_local_embedding_model(embedding_model_path, device=device)

    # 加载按照目录加载数据
    docs = DocsLoader().file_directory_loader(data_path)

    # 分块
    all_split_doc = []
    for doc in docs:
        split_docs = TextSpliter.text_split_by_manychar_or_charnum(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # 加上元数据，标题作为元数据
        for _ in split_docs:
            _.metadata = {'title': doc.metadata['source'].split()[-1].replace('.txt', '')}

        all_split_doc.extend(split_docs)

    # 保存到向量
    start = time.time()
    db = EmbeddingVectorDB.create_chroma_vector(all_split_doc, vector_db_path, embedding_model)
    end = time.time()
    print(f'向量库创建完成，耗时：{end - start}s')
