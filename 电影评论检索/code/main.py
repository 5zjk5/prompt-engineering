import pandas as pd
df1 = pd.read_excel('../data/春节档-评分_240227_1709000662.xlsx')
df2 = pd.read_excel('../data/春节档-评论_240227_1709000672.xlsx')
df1['数据类型'] = '电影分数'
df1.to_csv('../data/score.csv', index=False)
df2['数据类型'] = '电影评论'
df2.to_csv('../data/comment.csv', index=False)


from langchain_load_llm import LLM
from langchain_module import Chain, EmbeddingVectorDB, DocsLoader, TextSpliter, Retriever
from dotenv import load_dotenv
import warnings


# 加载 api
load_dotenv('../../key.env')
warnings.filterwarnings('ignore')

# llm
llm = LLM().zhipu_glm_4()

# embedding 模型
embedding_mode_path = '../../model/bge-small-zh-v1.5'
embedding_model = EmbeddingVectorDB.load_local_embedding_model(embedding_mode_path)

# 本地知识库加载，csv 的加载进来默认每一行是一个块，可以理解为分割过了
local_knowledge_score = '../data/score.csv'
local_knowledge_comment = '../data/comment.csv'
docs_score = DocsLoader.csv_loader(local_knowledge_score)
docs_comment = DocsLoader.csv_loader(local_knowledge_comment)
docs = docs_score + docs_comment

# 知识库向量化保存
movie_vector_path = '../data/movie_vector'
db = EmbeddingVectorDB.faiss_vector_db(docs, movie_vector_path, embedding_model)


query = '`周处除三害`这部电影的的平均评分是多少？'
retriever = Retriever.similarity(db, query, topk=100)
retriever
prompt = '''
参考以下信息回答问题：
```
{context}
```
--------------------------------
问题：{query}
'''
res = Chain.base_llm_chain(llm, prompt, query=query, context=retriever)
res


query = '春节期间上映了多少部电影？电影名称的字段为`name`'
langchian_retriever = Retriever.similarity(db, query, topk=len(docs))
langchian_retriever
# 使用 llmaindex 后处理过滤
from llamaindex_module import RetriverRank


retriever = RetriverRank.langchain_retriver_convert_NodeWithScore(langchian_retriever, query)
retriever = RetriverRank.keyword_node_postprocessor(retriever,  required_keywords=['电影分数'])
len(retriever)
prompt = '''
参考以下信息回答问题：
```
{context}
```
--------------------------------
问题：{query}
'''
res = Chain.base_llm_chain(llm, prompt, query=query, context=retriever)
res


query = '`怒潮`这部电影的评论主要讲了什么？'
langchian_retriever = Retriever.similarity_score_threshold(db, query, topk=100, score_threshold=0.3)
langchian_retriever
prompt = '''
参考以下信息回答问题：
```
{context}
```
--------------------------------
问题：{query}
'''
res = Chain.base_llm_chain(llm, prompt, query=query, context=langchian_retriever)
res
