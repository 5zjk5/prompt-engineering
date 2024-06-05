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
    db_path = '../data/similary.csv'
    data = pd.read_csv(db_path)
    data = data.head(100)
    start_time = time.time()
    batch_size = 3
    for i in range(0, len(data), batch_size):
        print(f'---------当前批次 {i}-{i + batch_size}/{len(data)}---------------------')
        try:
            df = data.iloc[i:i + batch_size, :]
            sentence1 = df['sentence1'].to_list()
            sentence2 = df['sentence2'].to_list()

            prompt = """
**标题：**句子相似度判断

**目的：**判断两句子（sentence1 和 sentence2）的语义相似度，考虑核心含义、语境、以及可能存在的实体型号差异。

**指导说明：**
- 仔细阅读sentence1和sentence2。
- 你的任务是评估这两个句子是否表达相同的概念或在语义上相近，考虑诸如语义和上下文等因素。
- 评估句子是否表达相同或非常接近的核心意义.
- 如果你认为句子意义相同或非常相似，输出 1。
- 如果句子在意义上存在重大差异，输出 0。
- 确保你的回答是 1 表示相似或 0 表示不相似，不需要提供额外的解释或理由。

**注意：**
- 如果两个句子主题不一样，那输出 0，例如：“a72充电插口”与“A7n充电接口”。
- 如果两个句子在对话情境中有相似的意图，那输出 1，例如：“你会讲什么方言”与“来几句方言听听”。
- 主语和宾语位置颠倒，那输出 0，例如：“我居然敢撩你”与“你居然敢撩我”。
- 若一句为疑问句式，另一句为陈述句式，即便内容接近，也视为表达不同意图，输出 0。例如，将“你是谁的小心肝”（疑问语气）与“你是不是我的小心肝”（疑问语气，尽管原说明有误，应同样视为疑问句）的情况，调整理解为对比“你是谁的小心肝”（疑问）与“你是我的小心肝”（陈述），则因语气不同，应输出 0。
- 两个句子即使语义上是相似的，但实际上指向的主体不一致，那应该输出 0，例如：“当我男朋友啦”与“我当你男朋友行不行”，第一句话是以女孩的角度，而第二句话是以男生的角度。

**示例格式：**
输入：
```
Sentence1: 她喜欢在月光下跳舞。
Sentence2: 在月光下跳舞是她最爱的消遣。
```
输出：1


输入：
```
Sentence1: 快速的棕色狐狸跳过篱笆。
Sentence2: 缓慢的灰色狗在桥下行走。
```
输出：0


轮到你了：
输入：
```
Sentence1: {sentence1}
Sentence2: {sentence2}
```
        """
            res = Chain.batch_base_llm_chain(model, prompt, max_concurrency=batch_size,
                                             sentence1=sentence1, sentence2=sentence2)

            for r in res:
                text = r['text'].split('输出：')[-1]
                sen1 = r['sentence1']
                sen2 = r['sentence2']
                pre.append(text)
                print(f'{sen1}\n{sen2}\n预测结果：{text}')
                print('---------------------------------')
            pass
        except Exception as e:
            traceback.print_exc()
            pass

    data['llm_res'] = pre
    data['label'] = data['label'].astype(str)
    data['correct'] = data.apply(lambda row: True if row['label'] in row['llm_res'] else False, axis=1)
    data.to_excel('../output/data_predit.xlsx', index=False)
    print('---------------------------------')
    print(f'预测正确率：', round(sum(data['correct']) / len(data) * 100, 2))

    end_time = time.time()
    print(f'用时：{end_time - start_time}s')
