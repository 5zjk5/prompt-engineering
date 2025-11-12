from rag.embedding_db import EmbeddingVectorDB
from rag.retriver import Retriever
from llm.llm_chain import base_llm_chain
from llm.llm_glm import *
import time
import json
import warnings


warnings.filterwarnings("ignore")

llm = zhipu_glm_4_long(temperature=0.1)

# 按照多少字分割，允许重叠多少字，召回个数
chunk_size = 1000
chunk_overlap = 20
topk = 150

# 本地调
embedding_model_path = r'D:\Python_project\NLP\model\bge-small-zh-v1.5'
device = 'cpu'
data_path = 'data/test_doc'
vector_db_path = f'data/all_doc_vector/all_doc_vector_{chunk_size}_metadata'

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

    # 加载 embedding 模型
    embedding_model = EmbeddingVectorDB.load_local_embedding_model(embedding_model_path, device)

    # 读取向量数据库
    db = EmbeddingVectorDB.load_chroma_vector(vector_db_path, embedding_model)

    # 循环每一个问题，先检索，再去回答
    answer_lines = []
    for i, line in enumerate(lines):
        print(f'----------{i + 1}/{len(lines)}-----------')
        cur_start_time = time.time()
        line = json.loads(line)
        id_ = line['id']
        query = line['question']
        print(f'query: {query}')

        # 召回方法
        retriver_doc = Retriever.similarity(db, query, topk=topk, long_context=True)
        # retriver_doc = [x.page_content for x in retriver_doc]
        retriver_doc_2 = Retriever.ensemble(query, retriver_doc, embedding_model, bm25_topk=25, topk=25, long_context=True)
        retriver_doc = [x.page_content for x in retriver_doc_2]

        full_prompt = prompt.format(retriver_doc=retriver_doc, query=query)
        llm_res = base_llm_chain(llm, full_prompt)
        answer_lines.append({'id': id_, 'answer': llm_res, 'retriver_doc': str(retriver_doc)})
        print(f'answer: {llm_res}')
        cur_end_time = time.time()
        print(f'spend time: {cur_end_time - cur_start_time}s')

    # 保存
    with open('data/all_doc_answer.json', "w+", encoding='utf-8') as json_file:
        for l in answer_lines:
            json_file.write(json.dumps(l, ensure_ascii=False) + '\n')

    end_time = time.time()
    print(f'总耗时：{end_time - start_time}s')
