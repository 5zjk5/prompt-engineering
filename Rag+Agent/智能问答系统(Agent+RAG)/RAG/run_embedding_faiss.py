# coding:utf8
import os
import time
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from utils.utils import get_file_size


def txt_loader(filepath):
    """
    加载 txt 数据
    :param filepath:
    :return:
    """
    loader = TextLoader(filepath, encoding='utf8')
    docs = loader.load()
    return docs


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
    docs = docs[0].page_content  # langchian 加载的 txt 转换为 str
    split_text = text_splitter.create_documents([docs])
    return split_text


def load_local_embedding_model(embedding_model_path, device='cpu'):
    """加载本地向量模型"""
    embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_path, model_kwargs={'device': device})
    return embedding_model


def faiss_vector_db(split_docs, vector_db_path, embedding_model):
    """
    https://python.langchain.com/docs/modules/data_connection/vectorstores/
    faiss 创建向量数据库
    :param split_docs: 分割的文本块
    :param vector_db_path: 向量数据库存储路径
    :param embedding_model: embedding 模型
    :return:
    """
    print('保存向量数据库路径 =》', vector_db_path)
    db = FAISS.from_documents(split_docs, embedding_model)
    db.save_local(vector_db_path)
    return db


if __name__ == '__main__':
    data_fold = '../data/dataset/pdf_txt_file_new/'
    file_list = os.listdir(data_fold)

    embedding_model_path = r'D:\Python_project\NLP\大模型学习\prompt-engineering\model\bge-small-zh-v1.5'
    embedding_model = load_local_embedding_model(embedding_model_path)

    start_time = time.time()
    for index, file in enumerate(file_list):
        print(f'-----{index + 1} / {len(file_list)}-----')
        print(f'当前文件：{file}，大小：{get_file_size(data_fold + file)}')
        cur_start_time = time.time()
        docs = txt_loader(data_fold + file)
        split_text = text_split_by_manychar_or_charnum(docs, chunk_size=256, chunk_overlap=20)

        new_split_text = []
        for text in split_text:
            text.metadata['source'] = file
            new_split_text.append(text)

        faiss_vector_db(new_split_text, '../data/vector', embedding_model)
        cur_end_time = time.time()
        print(f'当前文件耗时：{cur_end_time - cur_start_time}s')
        pass

    end_time = time.time()
    print(f'耗时：{end_time - start_time}s')
