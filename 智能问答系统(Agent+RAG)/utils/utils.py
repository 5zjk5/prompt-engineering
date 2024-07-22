# coding:utf8
import jsonlines
import re
import os
from utils.prompts import glml4_classification_prompt, glml4_rag_retriver_prompt
from llm.llm_chain import str_chain, base_llm_chain
from RAG.retriver import retriever_docs


def read_jsonl(path):
    content = []
    with jsonlines.open(path, "r") as json_file:
        for obj in json_file.iter(type=dict, skip_invalid=True):
            content.append(obj)
    return content


def write_jsonl(path, content):
    """
    content: [{}, {}...]
    """
    with jsonlines.open(path, "w") as json_file:
        json_file.write_all(content)


def classify_question(question, llm):
    """
    问题分类
    sql：需要查询 sql 的类别
    招股说明书：跟招股说明书相关的类别
    输出结果以 json 输出 {'classification': xxx, 'reason': xxx}
    """
    res = str_chain(question, glml4_classification_prompt, llm)
    res = res.replace('\n', '')
    res = re.findall('(\{.*?\})', res)
    if res:
        classification = eval(res[0])['classification']
    else:
        classification = '招股、sql'
    return classification


def get_file_size(file_path):
    # 获取文件大小
    file_size_bytes = os.path.getsize(file_path)
    # 将文件大小转换为MB
    file_size_mb = file_size_bytes / (1024 ** 2)
    return file_size_mb


def rag_answer(question, llm):
    """
    招股书 rag
    """
    retriever_res = retriever_docs(question, llm, topk=50, retriver_way='self_query')
    answer = base_llm_chain(llm, glml4_rag_retriver_prompt, question=question, retriver_res=retriever_res)
    return answer
