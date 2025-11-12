# coding:utf8
import os
import base64
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from prompt.prompts import glml4_rag_retriver_prompt
from llm.llm_chain import base_llm_chain


data_path = 'data/dataset/pdf_txt_file_new'
file_list = os.listdir(data_path)
file_name = [file.split('.')[0] for file in file_list]
embedding_model_path = r'D:\Python_project\NLP\大模型学习\prompt-engineering\model\bge-small-zh-v1.5'
embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_path, model_kwargs={'device': 'cpu'})


def retriver_by_rule(question, glm4, print):
    # 判断招股书的文件名（公司名）是否在问题中
    for company in file_name:
        if company.strip(' 。') in question:
            print(f'有对应招股书-{company}')
            with open(os.path.join(data_path, company + '.txt'), 'r', encoding='utf-8') as f:
                text = f.read()
                break
    # 都不包含则读入所有文件
    else:
        # print(f'没有找到招股书，全部读入')
        # company = 'all_text'
        # text = get_docs_lst()
        return '没有找到招股书，放弃检索！'

    # 编码为非中文
    company = base64.b64encode(company.encode('utf-8')).decode('utf-8')

    # 根据招股书，分块；创建向量或读取；检索
    split_text = text_split_by_manychar_or_charnum(text, chunk_size=1000, chunk_overlap=20)
    vector_db = faiss_vector_db(split_text, f'RAG/faiss_db/{company}', embedding_model)
    retriever_docs = similarity(vector_db, question, topk=20)

    # llm 回答
    answer = base_llm_chain(glm4, glml4_rag_retriver_prompt, print, question=question, retriver_res=retriever_docs)
    return answer


def text_split_by_manychar_or_charnum(docs, separator=["\n\n", "\n", " ", ""], chunk_size=100, chunk_overlap=20,
                                      length_function=len, is_separator_regex=True):
    """
    https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter/
    按照 chunk_size 字数分割，separator 不需要传，保持默认值即可
    多个字符拆分，separator 指定，符合列表中的字符就会被拆分
    :param docs: 文档，必须为 str，如果是 langchain 加载进来的需要转换一下
    :param separator: 分割字符，默认以列表中的字符去分割 ["\n\n", "\n", " ", ""]
    :param chunk_size: 每块大小
    :param chunk_overlap: 允许字数重叠大小
    :param length_function:
    :param is_separator_regex:
    :return:
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,  # 指定每块大小
        chunk_overlap=chunk_overlap,  # 指定每块可以重叠的字符数
        length_function=length_function,
        is_separator_regex=is_separator_regex,
        separators=separator  # 指定按照什么字符去分割，如果不指定就按照 chunk_size +- chunk_overlap（100+-20）个字去分割
    )
    split_text = text_splitter.create_documents([docs])
    return split_text


def faiss_vector_db(split_docs, vector_db_path, embedding_model):
    """
    https://python.langchain.com/docs/modules/data_connection/vectorstores/
    faiss 创建向量数据库
    :param split_docs: 分割的文本块
    :param vector_db_path: 向量数据库存储路径
    :param embedding_model: embedding 模型
    :return:
    """
    if os.path.exists(vector_db_path):
        print('加载向量数据库路径 =》', vector_db_path)
        db = FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)
    else:
        print('创建向量数据库路径 =》', vector_db_path)
        db = FAISS.from_documents(split_docs, embedding_model)
        db.save_local(vector_db_path)
    return db


def similarity(db, query, topk=5):
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
    return retriever_docs
