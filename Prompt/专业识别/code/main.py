from langchain_load_llm import LLM
from langchain_module import Chain, EmbeddingVectorDB, DocsLoader, TextSpliter, Retriever
from dotenv import load_dotenv
import pandas as pd
import time
import warnings


# 加载 api
load_dotenv('../../key.env')
warnings.filterwarnings('ignore')


if __name__ == '__main__':
    # llm
    model = LLM().tongyi_qwen_plus(temperature=1)

    # embedding 模型
    embedding_mode_path = '../../model/bge-small-zh-v1.5'
    embedding_model = EmbeddingVectorDB.load_local_embedding_model(embedding_mode_path)

    # 本地知识库加载
    local_knowledge = '../data/label_info.txt'
    docs = DocsLoader.txt_loader(local_knowledge)

    # 知识库分割
    text_split = TextSpliter.text_split_by_char(docs, separator='\n', chunk_size=20, chunk_overlap=0)

    # 知识库向量化保存
    vector_db_path = '../data/label_info_vector'
    db = EmbeddingVectorDB.faiss_vector_db(text_split, vector_db_path, embedding_model)

    # 预测数据
    recall_cnt = 0
    pre = []
    db_path = '../data/classfield_data.csv'
    data = pd.read_csv(db_path)
    data = data.head(100)
    start_time = time.time()
    for index, row in data.iterrows():
        print(f'----------{index + 1}/{len(data)}----------')
        content = row['content']
        label = row['label']
        print(f'当前数据 {content}\n当前标签 {label}')

        # 召回相似的文档，对比所有方法，看看哪个召回率高
        # retriever_label = Retriever.similarity(db, content, topk=30)  # 0.95
        # retriever_label = Retriever.similarity_with_score(db, content, topk=30)  # 0.95
        # retriever_label = [doc[0].page_content.split('\t')[0] for doc in retriever_label]
        # retriever_label = Retriever.mmr(db, content, topk=30)  # 0.645
        # retriever_label = Retriever.similarity_score_threshold(db, content, topk=30, score_threshold=0.2)  # 0.425
        # retriever_label = Retriever.contextual_compression_by_embedding(db, content, embedding_model, topk=30,
        #                                                                 similarity_threshold=0.2)  # 0.91
        # retriever_label = Retriever.contextual_compression_by_embedding_split(db, content, embedding_model, topk=30,
        #                                                                 similarity_threshold=0.2, chunk_size=10)  # 0.91
        # retriever_label = Retriever.ensemble(content, text_split, embedding_model, bm25_topk=15, topk=15) # 0.905
        # retriever_label = Retriever.bm25(content, text_split, topk=30)  # 0.465
        # retriever_label, parent_docs = Retriever.parent_document_retriever(docs, content, embedding_model)
        # retriever_label = [doc.page_content.split('\n') for doc in retriever_label]
        # retriever_label = [d.split('\t')[0] for doc in retriever_label for d in doc]  # 0.295
        # retriever_label = Retriever.tfidf(content, [doc.page_content.split('\n') for doc in docs][0])  # 0.075
        # retriever_label = Retriever.knn(content, [doc.page_content.split('\n') for doc in docs][0], embedding_model)  # 0.685
        # retriever_label = Retriever.multi_query_retriever(db, content, model)  # 0.79
        # retriever_label = Retriever.contextual_compression_by_llm(db, content, model)  # 模型能力不行

        # 召回标签
        retriever_label = Retriever.similarity(db, content, topk=30)
        retriever_label = [doc.page_content.split('\t')[0] for doc in retriever_label]
        if label in retriever_label:
            print('召回')
            recall_cnt += 1

        prompt = f"""
**角色设定：**
你是一个专业分类专家，你能帮助用户识别描述中的专业。
        
**任务：**
你需要识别描述中的专业，并从专业列表中选出出最相关的专业名称。
        
**决策规则：**
- 给出的专业必须来自于专业列表中列出的专业。
- 仔细分析描述中出现的专业名词，判断它们是否指向特定的专业。
- 让我们一步一步来思考。
- 识别出最相关的专业名称。
        
**输出：**
- 直接输出选出的专业名称，以及你的推理过程。
        
**以下是描述及专业列表：**
- 描述：{content}
- 专业列表：{retriever_label}
"""
        res = Chain.base_llm_chain(model, prompt)
        pre.append(res)
        print(f'预测结果：{res}')
        pass

    data['llm_res'] = pre
    data['correct'] = data.apply(lambda row: True if row['label'] in row['llm_res'] else False, axis=1)
    data.to_excel('../output/classfield_data_predit.xlsx', index=False)
    print('---------------------------------')
    print(f'预测正确率：', round(sum(data['correct']) / len(data) * 100, 2))
    print(f'召回率：{recall_cnt / len(data)}')

    end_time = time.time()
    print(f'用时：{end_time - start_time}s')
