import time
import json
import os
from rag.load_data import DocsLoader
from rag.doc_split import TextSpliter
from llm.llm_glm import zhipu_glm_4_flash, zhipu_glm_4_long
from llm.llm_chain import base_llm_chain
from langchain_module import EmbeddingVectorDB
from langchain.vectorstores import Neo4jVector



llm = zhipu_glm_4_long()

# neo4j 凭证
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "12345678"

# 按照多少字分割，允许重叠多少字
chunk_size = 1000
chunk_overlap = 20


def load_doc():
    data_path = ['data/pdf', 'data/word', 'data/markdown', 'data/txt', ]
    # data_path = ['data/txt', ]
    # 加载按照目录加载数据
    docs = []
    for path in data_path:
        if 'word' in path:
            for file in os.listdir(path):
                docs.extend(DocsLoader().word_loader(os.path.join(path, file)))
        elif 'pdf' in path:
            docs.extend(DocsLoader().pdf_loader(path, is_directory=True))
        else:
            docs.extend(DocsLoader().file_directory_loader(path))

    # 分块
    all_split_doc = []
    for doc in docs:
        split_docs = TextSpliter.text_split_by_manychar_or_charnum(doc, chunk_size=chunk_size,
                                                                   chunk_overlap=chunk_overlap)

        # 加上元数据，标题作为元数据
        for _ in split_docs:
            _.metadata = {'title': doc.metadata['source'].split()[-1].replace('.txt', '')}

        all_split_doc.extend(split_docs)

    return all_split_doc


def neo4j_vector_obj(documents):
    # 实例化 Neo4j 向量
    neo4j_vector = Neo4jVector.from_documents(
        documents,
        embedding,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD
    )
    return neo4j_vector


prompt = """
# 参考以下信息回答问题：
```
{retriver_doc}
```
----------------------------------------
# 问题：
```
{query}
```
"""


if __name__ == '__main__':
    start_time = time.time()

    with open('data/doc_question.json', encoding='utf8') as f:
        lines = f.readlines()

    embedding = EmbeddingVectorDB.load_local_embedding_model(r'D:\Python_project\NLP\model\bge-small-zh-v1.5')

    all_split_doc = load_doc()
    neo4j_vector = neo4j_vector_obj(all_split_doc)

    # 循环每一个问题，先检索，再去回答
    answer_lines = []
    for i, line in enumerate(lines):
        print(f'----------{i + 1}/{len(lines)}-----------')
        cur_start_time = time.time()
        line = json.loads(line)
        id_ = line['id']
        query = line['question']
        print(f'query: {query}')

        retriver_doc = neo4j_vector.similarity_search(query=query, k=50)
        retriver_doc = [r.page_content for r in retriver_doc]
        full_prompt = prompt.format(retriver_doc=retriver_doc, query=query)
        llm_res = base_llm_chain(llm, full_prompt)

        print(f'answer: {llm_res}')
        cur_end_time = time.time()
        print(f'spend time: {cur_end_time - cur_start_time}s')

    end_time = time.time()
    print(f'总耗时：{end_time - start_time}s')
