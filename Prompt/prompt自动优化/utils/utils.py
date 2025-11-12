# coding:utf-8
import pandas as pd
import os
import logging
import sys
import time
import re
import traceback
from llm.llm_chain import base_llm_chain, batch_base_llm_chain
from config.config import get_full_prompt, predit_batch_size, select_input_query, income_var, income_var_lst
from prompt.prompt import output_json_format_prompt, analyze_prompt, optimize_prompt


def log_handle(output_fold):
    """创建日志"""
    output_path = 'data/output_data'

    # 创建一个日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 创建一个日志处理器，用于将日志写入文件
    file_handler = logging.FileHandler(os.path.join(output_path, output_fold, 'output.log'), mode='w')
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


def load_data(input_data, log):
    """读取数据"""
    input_path = 'data/input_data'
    if 'csv' in input_data:
        try:
            data = pd.read_csv(os.path.join(input_path, input_data))
        except:
            data = pd.read_csv(os.path.join(input_path, input_data), encoding='gbk')
    elif 'xlsx' in input_data:
        try:
            data = pd.read_excel(os.path.join(input_path, input_data))
        except:
            data = pd.read_excel(os.path.join(input_path, input_data), engine='xlrd')

    if 'label' not in data.columns:
        log(f'缺少 label 列，请检查数据')
        exit(0)
    return data


def make_output_folder(output_fold):
    """创建输出文件夹"""
    output_path = 'data/output_data'
    os.makedirs(os.path.join(output_path, output_fold), exist_ok=True)


def predit_data(data, llm, cur_prompt, log):
    """预测数据，一条一条预测"""
    llm_res_lst = []
    reason_lst = []
    error_cnt = 0
    log(f'当前格式输出控制 prompt：{output_json_format_prompt}')
    start_time = time.time()
    for index, row in data.iterrows():
        cur_start_time = time.time()
        log(f'开始预测第 {index + 1}/{len(data)} 条数据')

        # 根据每一行数据传入变量拼接 prompt，并控制输出 json 格式
        full_prompt = get_full_prompt(row, cur_prompt)
        full_prompt += '\n' + output_json_format_prompt

        # 预测
        try:
            llm_response = base_llm_chain(llm, full_prompt)
            log(f'llm_res: {llm_response}')
            llm_res, reaseon = parse_llm_response(llm_response)
        except Exception as err:
            error_cnt += 1
            log(f'{traceback.format_exc()}')
            llm_res = reaseon = str(err)
        llm_res_lst.append(llm_res)
        reason_lst.append(reaseon)

        cur_end_time = time.time()
        log(f'预测第 {index + 1}/{len(data)} 条数据 end！耗时：{cur_end_time - cur_start_time} s')
        log(f'-----------------------------------------------------------')

    data['llm_res'] = llm_res_lst
    data['reason'] = reason_lst
    end_time = time.time()
    log(f'预测数据 end！耗时：{end_time - start_time} s，错误次数：{error_cnt}')
    return data


def predit_data_batch(data, llm, cur_prompt, log):
    """预测数据，批次预测"""
    llm_res_lst = []
    reason_lst = []
    error_cnt = 0
    log(f'当前格式输出控制 prompt：{output_json_format_prompt}')
    start_time = time.time()
    for batch in range(0, len(data), predit_batch_size):
        cur_start_time = time.time()
        log(f'开始预测第 {batch + predit_batch_size}/{len(data)} 批次')
        df = data.iloc[batch:batch + predit_batch_size,:]

        batch_prompt = []
        for index, row in df.iterrows():
            # 根据每一行数据传入变量拼接 prompt，并控制输出 json 格式
            full_prompt = get_full_prompt(row, cur_prompt)
            full_prompt += '\n' + output_json_format_prompt
            batch_prompt.append(full_prompt)

        # 预测
        try:
            llm_response = batch_base_llm_chain(llm, '{batch_prompt}', max_concurrency=predit_batch_size,
                                                batch_prompt=batch_prompt)
        except Exception as err:
            log(f'批次预测报错，{traceback.print_exc()}')
            llm_response = [{"text": {"llm_res": "error", "reason": "error"}} for i in range(len(batch_prompt))]
        log(f'llm_res: {llm_response}')
        for res in llm_response:
            res = res['text']
            llm_res, reaseon = parse_llm_response(res)
            llm_res_lst.append(llm_res)
            reason_lst.append(reaseon)

        cur_end_time = time.time()
        log(f'预测第 {batch + predit_batch_size}/{len(data)} 批次 end！耗时：{cur_end_time - cur_start_time} s')

    data['llm_res'] = llm_res_lst
    data['reason'] = reason_lst
    end_time = time.time()
    log(f'预测数据 end！耗时：{end_time - start_time} s，错误次数：{error_cnt}')
    return data


def parse_llm_response(response):
    response = response.replace('`', '').replace('json', '').strip('":')
    try:
        llm_res = eval(response)['llm_res']
        reaseon = eval(response)['reason']
    except Exception as err:
        llm_res = reaseon = str(err)
    return llm_res, reaseon


def analyze_data(data, llm, cur_prompt, log):
    """
    分析结果，并优化得到新的 prompt
    step1: 区分正确，错误样本，保证 1:1，如果错误样本较多，可以从正确的里面抽取重复的
    step2: 每次正确，错误各选几条条组合去分析，数量可控 sample_cnt，传入 prompt 模版
    step3: 得到的多组结果与 prompt 模版一起送给模型去优化改进得到新的 prompt
    """
    log(f'开始分析结果，当前分析的 prompt：{cur_prompt}')
    start_time = time.time()

    # step1
    correct_data = data[data['eval_res'] == 1]
    error_date = data[data['eval_res'] == 0]
    correct_cnt, error_cnt = len(correct_data), len(error_date)
    if error_cnt > correct_cnt:
        log(f'错误样本数量大于正确样本数量，从正确样本中抽取重复的样本')
        correct_data_sample = correct_data.sample(n=error_cnt - correct_cnt, replace=True)
        correct_data = pd.concat([correct_data, correct_data_sample])
    correct_data = correct_data.reset_index(drop=True).head(error_cnt)

    # step2
    history = []
    sample_cnt = 3
    log(f'当前分析的 prompt: {analyze_prompt}')
    for i in range(0, error_cnt, sample_cnt):
        log(f'开始分析第 {i + sample_cnt}/{error_cnt} 条错误样本和正确样本')
        df_correct = correct_data.iloc[i:i + sample_cnt, :]
        df_error = error_date.iloc[i: i + sample_cnt, :]
        df = pd.concat([df_correct, df_error])

        # 列选择
        df = select_input_query(df)
        df = df.to_string(index=False)

        full_analyze_prompt = analyze_prompt.format(df=df, cur_prompt=cur_prompt)
        full_analyze_prompt = full_analyze_prompt.replace('{', '{{').replace('}', '}}')
        try:
            llm_response = base_llm_chain(llm, full_analyze_prompt)
        except Exception as err:
            log(f'{traceback.format_exc()}')
            log(f'当前错误 prompt: {full_analyze_prompt}')
            llm_response = str(err)
        log(f'分析结果 llm_response: {llm_response}')
        history.append(llm_response)

    end_time = time.time()
    log(f'分析结果 end!，耗时：{end_time - start_time} s')

    # step3
    log(f'当前优化的 prompt：{optimize_prompt}')
    full_optimize_prompt = optimize_prompt.format(history='\n======================================='.join(history),
                                                  cur_prompt=cur_prompt)
    full_optimize_prompt = full_optimize_prompt.replace('{', '{{').replace('}', '}}')
    try:
        llm_response = base_llm_chain(llm, full_optimize_prompt)
    except Exception as err:
        log(f'{traceback.format_exc()}')
        log(f'当前错误 prompt: {full_optimize_prompt}')
        llm_response = cur_prompt
    # if income_var not in llm_response:
    #     llm_response += income_var
    for l in income_var_lst:
        if l not in llm_response:
            llm_response += income_var
            break
    log(f'优化后的提示词 llm_response: {llm_response}')

    return llm_response


def del_prompt_var(data, cur_prompt, log):
    """
    data 用来获取 row，删除提示词中多余的变量，利用 KeyError 编写规则比 llm 去剔除，更稳定
    如果一直在这循环，检查 config 中是否有哪个变量没写对，多字母啥的
    """
    while True:
        log(f'删除多余变量前的提示词：{cur_prompt}')
        for index, row in data.iterrows():
            pass
        try:
            full_prompt = get_full_prompt(row, cur_prompt)
            break
        except KeyError as err:
            key = re.findall("'(.*)'", str(err))[0]
            key = '{' + key + '}'
            cur_prompt = cur_prompt.replace(key, '')
        log(f'删除多余变量后的提示词：{cur_prompt}')
    return cur_prompt
