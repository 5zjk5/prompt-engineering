# coding:utf8
import jsonlines
import re
import os
import sys
import logging
from prompt.prompts import glml4_classification_prompt
from llm.llm_chain import base_llm_chain


def log_handle():
    """创建日志"""
    output_path = 'data/'

    # 创建一个日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 创建一个日志处理器，用于将日志写入文件
    file_handler = logging.FileHandler(os.path.join(output_path, 'output.log'), mode='w')
    file_handler.setLevel(logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 将日志处理器添加到日志记录器
    logger.addHandler(file_handler)

    # 创建一个 StreamHandler，用于捕获标准输出
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # 将 StreamHandler 添加到 logger
    logger.addHandler(stream_handler)

    # 重定向 print 到 logger.info
    def log_print(*args, **kwargs):
        logger.info(' '.join(map(str, args)), **kwargs)

    # 替换内置的 print 函数
    print = log_print

    return print


def read_jsonl(path):
    content = []
    with jsonlines.open(path, "r") as json_file:
        for obj in json_file.iter(type=dict, skip_invalid=True):
            content.append(obj)
    return content


def create_write_jsonl(path):
    """
    content: [{}, {}...]
    """
    with jsonlines.open(path, "w") as json_file:
        pass


def write_jsonl(path, content):
    """
    content: [{}, {}...]
    """
    with jsonlines.open(path, "a") as json_file:
        json_file.write_all(content)


def classify_question(question, llm, print):
    """
    问题分类
    sql：需要查询 sql 的类别
    招股说明书：跟招股说明书相关的类别
    输出结果以 json 输出 {'classification': xxx, 'reason': xxx}
    """
    res = base_llm_chain(llm, glml4_classification_prompt, print, question=question)
    res = res.replace('\n', '')
    res = re.findall('(\{.*?\})', res)
    if res:
        classification = eval(res[0])['classification']
    else:
        classification = '招股、sql'
    return classification


def calc_token(print):
    """计算当前问题用了多少 token"""
    with open('data/output.log', 'r') as f:
        log = f.read()
    logs = re.findall(r'==================================================================(.*?)==================================================================',
                      log, re.S)
    tokens = re.findall(r'/总共 token：(\d+)/', logs[0])
    tokens = sum([int(t) for t in tokens])
    print(f'当前问题用了 {tokens} tokens')
