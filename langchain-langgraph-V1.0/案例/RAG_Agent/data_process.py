import os
import time
from data_loader import DataLoader
from data_split import DataSplit
from data_embedding import DataEmbedding
from data_embedding_to_vector import EmbeddingVector
from data_retrieval import DataRetrieval


def load_data_by_type(data_files: list):
    """根据数据类型加载数据"""
    docs = []
    for file in data_files:
        if file.endswith('.pdf'):
            docs.extend(DataLoader.load_pdf(file))
        elif file.endswith('.docx'):
            docs.extend(DataLoader.load_docx(file))
        elif file.endswith('.csv'):
            docs.extend(DataLoader.load_csv(file))
        elif file.endswith('.html'):
            docs.extend(DataLoader.load_html(file))
        elif file.endswith('.json') or file.endswith('.jsonl'):
            docs.extend(DataLoader.load_json(file))
        elif file.endswith('.md'):
            docs.extend(DataLoader.load_markdown(file))
        else:
            docs.extend(DataLoader.load_other(file))

    return docs


def spliter_docs(docs):
    """切分文档"""
    split_docs = []
    for doc in docs:
        if doc.metadata['source'].endswith('.md'):
            split_docs.extend(DataSplit.split_md(doc))
        elif doc.metadata['source'].endswith('.json') or doc.metadata['source'].endswith('.jsonl'):
            split_docs.extend(DataSplit.split_json(doc))
        elif doc.metadata['source'].endswith('.py'):
            split_docs.extend(DataSplit.split_code(doc))
        elif doc.metadata['source'].endswith('.csv'):
            split_docs.append(doc)
        elif doc.metadata['source'].endswith('.html'):
            split_docs.append(doc)
        else:
            split_docs.extend(DataSplit.split_other(doc))
    return split_docs


if __name__ == '__main__':
    data_dir = './data'
    data_files = [os.path.join(data_dir, data_file) for data_file in os.listdir(data_dir)]
    print(f'data_files: {data_files}')

    start_time = time.time()
    docs = load_data_by_type(data_files)
    end_time = time.time()
    print(f'加载数据用时: {end_time - start_time} doc 长度：{len(docs)}')

    start_time = time.time()
    split_docs = spliter_docs(docs)
    end_time = time.time()
    print(f'分割数据用时: {end_time - start_time} split_docs 长度：{len(split_docs)}')

    embedding_model = DataEmbedding().init_embedding_model()
    print(f'embedding 模型连接完成')

    start_time = time.time()
    memory_store, chrome_store, faiss_store = EmbeddingVector().to_vector(split_docs, embedding_model)
    end_time = time.time()
    print(f'入库总用时: {end_time - start_time}')

    # 检索
    data_retrieval = DataRetrieval(embedding_model, memory_store, chrome_store, faiss_store)
    query = "护发用什么好？"
    data_retrieval.retrieval(query)
