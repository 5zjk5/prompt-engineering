# coding:utf8
import time
import os
import traceback
from config.config import (
    llm, input_data, output_fold, epoch, init_prompt, batch_switch, eval_fun
)
from utils.utils import (
    load_data, make_output_folder, log_handle, predit_data, predit_data_batch, analyze_data, del_prompt_var
)


def predit(data, llm, cur_prompt, log):
    """预测数据"""
    if batch_switch:
        data = predit_data_batch(data, llm, cur_prompt, log)
    else:
        data = predit_data(data, llm, cur_prompt, log)
    return data


if __name__ == '__main__':
    start_time = time.time()

    # 创建输出文件夹
    make_output_folder(output_fold)

    # 创建日志
    log = log_handle(output_fold)

    try:
        # 读取数据
        data = load_data(input_data, log)
        data = data.head(100)

        # 开是循环每一轮
        best_prompt = init_prompt
        best_acc = 0
        cur_prompt = init_prompt
        for e in range(epoch):
            epoch_start_time = time.time()
            log(f'第 {e + 1} 轮 begin，共 {epoch} 轮...')

            # 预测数据
            try:
                data = predit(data, llm, cur_prompt, log)
            except KeyError as err:  # 生成的提示词有多余的变量，即 {xxx} 括起来的，需要删除
                log(f'当前提示词有多余的变量，删除优化.')
                cur_prompt = del_prompt_var(data.head(1), cur_prompt, log)
                data = predit(data, llm, cur_prompt, log)

            # 评估数据
            data, cur_acc = eval_fun(data, log)
            log(f'第 {e + 1} 轮，当前准确率：{cur_acc}')
            if cur_acc > best_acc:
                best_prompt = cur_prompt
                best_acc = cur_acc
                log(f'最优更新！最优准确率：{best_acc}\n最优 prompt：{best_prompt}，')
                data.to_excel(os.path.join('data/output_data/', output_fold, f'{e + 1}_best_eval.xlsx'), index=False)
            else:
                cur_prompt = best_prompt

            # 如果是最后一轮评估完毕，则退出循环
            if e + 1 == epoch:
                break

            # 分析结果，并优化得到新的 prompt
            new_prompt = analyze_data(data, llm, cur_prompt, log)
            cur_prompt = new_prompt

            epoch_end_time = time.time()
            log(f'第 {e + 1} 轮 end，共 {epoch} 轮，耗时 {epoch_end_time - epoch_start_time:.2f}s')

    except Exception as err:
        log(traceback.format_exc())
        best_prompt = init_prompt
        best_acc = None

    log(f'end all 最优准确率：{best_acc}\n最优 prompt：{best_prompt}，')
    end_time = time.time()
    log(f'总共耗时 {end_time - start_time:.2f}s')
