from langchain_load_llm import LLM
from langchain_module import Chain
from dotenv import load_dotenv
import pandas as pd
import time
import warnings
import traceback


# 加载 api
load_dotenv('../../key.env')
warnings.filterwarnings('ignore')


if __name__ == '__main__':
    # llm
    model = LLM().tongyi_qwen_14b_chat(temperature=1)

    pre = []
    db_path = '../data/emotion.csv'
    data = pd.read_csv(db_path, encoding='gbk')
    data = data.head(100)
    start_time = time.time()
    batch_size = 3
    for i in range(0, len(data), batch_size):
        print(f'---------当前批次 {i}-{i + batch_size}/{len(data)}---------------------')
        try:
            df = data.iloc[i:i + batch_size, :]
            sentenece = df['sentenece'].to_list()

            prompt = """
    **角色身份：**
    作为情感倾向鉴定专家，你利用情感分析技巧来判定文本的情感色彩。
    
    **任务概述：**
    针对一系列商品评论，你的职责是迅速识别每条评论的情感倾向——是积极正面还是消极负面。
    
    **执行指南：**
    - 针对每段给定的评论文本，进行情感倾向判断。
    - 若评论表达的是积极情绪，直接输出：Positive
    - 若评论倾向于消极情绪，直接输出：Negative
    - 输出时无需附带任何解释或额外信息。
    - 必须选择输出“Positive”或“Negative”，例如`跑步很合适，但是做工不佳，连接性也不是很便利`这段文本虽然说是正面情绪，但是实际是负面情绪，所以应该输出Negative。
    
    **待分析评论样本：**
    {sentenece}
    
    请依据上述准则，对提供的评论进行情感倾向判断并给出简洁的响应。
        """
            res = Chain.batch_base_llm_chain(model, prompt, max_concurrency=batch_size, sentenece=sentenece)

            for r in res:
                text = r['text']
                sen = r['sentenece']
                pre.append(text)
                print(f'{sen}\n预测结果：{text}')
            pass
        except Exception as e:
            traceback.print_exc()
            pass

    data['llm_res'] = pre
    data['correct'] = data.apply(lambda row: True if row['label'] in row['llm_res'] else False, axis=1)
    data.to_excel('../output/data_predit.xlsx', index=False)
    print('---------------------------------')
    print(f'预测正确率：', round(sum(data['correct']) / len(data) * 100, 2))

    end_time = time.time()
    print(f'用时：{end_time - start_time}s')
