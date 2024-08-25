# coding:utf8

# api key env 文件路径
api_env_path = r'D:\Python_project\NLP\大模型学习\prompt-engineering\key.env'

# 大模型选择
from llm.llm_glm import zhipu_glm_4_air
llm = zhipu_glm_4_air(temperature=0.1)

# 输入数据
input_data = 'similary.csv'

# 输出文件夹，不需要修改，修改 input_data 会自动改
output_fold = input_data.split('.')[0]

# 最大轮数
epoch = 3

# 是否开启批次调用
batch_switch = True

# 批次预测数据量
predit_batch_size = 70

# 初始 prompt
init_prompt = """
**标题：**句子相似度判断

**目的：**判定两个句子，sentence1 和 sentence2，是否传达相同的含义或在本质上相似。

**指导说明：**
- 仔细阅读sentence1和sentence2。
- 你的任务是评估这两个句子是否表达相同的概念或在语义上相近，考虑诸如语义和上下文等因素。
- 如果你认为句子意义相同或非常相似，输出 1。
- 如果句子在意义上存在重大差异，输出 0。
- 确保你的回答是 1 表示相似或 0 表示不相似，不需要提供额外的解释或理由。

**示例格式：**
输入：
Sentence1: 她喜欢在月光下跳舞。 
Sentence2: 在月光下跳舞是她最爱的消遣。
输出：1

输入：
Sentence1: 快速的棕色狐狸跳过篱笆。 
Sentence2: 缓慢的灰色狗在桥下行走。
输出：0

轮到你了：
输入：
Sentence1: {sentence1} 
Sentence2: {sentence2}
"""

# 输入变量模版
income_var = """
输入：
Sentence1: {sentence1} 
Sentence2: {sentence2}
"""

# 输入变量列表，每个变量用 {} 括起来，字符串
income_var_lst = ['{sentence1}', '{sentence2}']


# 定义获得变量后拼接完整 prompt 函数
def get_full_prompt(row, cur_prompt):
    """根据输入数据，进行修改字段，format" 中的字段要修改"""
    sentence1 = row['sentence1']
    sentence2 = row['sentence2']

    full_prompt = cur_prompt.format(sentence1=sentence1, sentence2=sentence2)
    return full_prompt


# 动态获取数据输入，有些 query 可能是一列，有些可能是多列,主要用于分析函数中的列选择
def select_input_query(df):
    """像这个例子，数据输入列主要是 sentence1', 'sentence2' ，后面三列是必选的"""
    df = df[['sentence1', 'sentence2', 'label', 'llm_res', 'reason']]
    return df


# 评估函数，需要根据不同数据自定义函数到 evals 模块
from evals.eval_similary import eval_similary
eval_fun = eval_similary
