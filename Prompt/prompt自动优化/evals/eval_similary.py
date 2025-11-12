# coding:utf8

def eval_similary(data, log):
    """评估句子相似度函数"""
    data['llm_res'] = data['llm_res'].astype(int)
    data['label'] = data['label'].astype(int)
    data['eval_res'] = (data['llm_res'] == data['label'])
    data['eval_res'] = data['eval_res'].apply(lambda x: 1 if x else 0)
    correct_num = len(data[data['eval_res'] == 1])
    error_num = len(data[data['eval_res'] == 0])
    acc = round(correct_num / len(data) * 100, 2)
    log(f'正确率：{acc}% 正确数：{correct_num} 错误数：{error_num}')
    return data, acc
