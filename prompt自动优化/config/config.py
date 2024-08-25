# coding:utf8

# api key env 文件路径
api_env_path = r'D:\Python_project\NLP\大模型学习\prompt-engineering\key.env'

# 大模型选择
from llm.llm_glm import zhipu_glm_4_air
llm = zhipu_glm_4_air(temperature=0.1)

# 输入数据
input_data = 'emotion.csv'

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
角色设定：
你是一个情感分析专家，擅长通过情感分析技术，给出情感分析结果。

背景：
有一些商品的评论数据，现在需要判断每一条评论是积极的，还是属于消极的。

任务：
给你提供一段评论的文本，你需要判断这段评论是属于积极的，还是属于消极的。

输出：
- 如果判断为积极的，请输出`Positive`，不需要输出理由及其他任何信息。
- 如果判断为消极的，请输出`Negative`，不需要输出理由及其他任何信息。

以下是需要判断的文本：
`{sentence}`
"""

# 输入变量模版
income_var = """
以下是需要判断的文本：
`{sentence}`
"""

# 输入变量列表，每个变量用 {} 括起来，字符串
income_var_lst = ['{sentence}']


# 定义获得变量后拼接完整 prompt 函数
def get_full_prompt(row, cur_prompt):
    """根据输入数据，进行修改字段，format" 中的字段要修改"""
    sentence = row['sentenece']

    full_prompt = cur_prompt.format(sentence=sentence)
    return full_prompt


# 动态获取数据输入，有些 query 可能是一列，有些可能是多列,主要用于分析函数中的列选择
def select_input_query(df):
    """像这个例子，数据输入列主要是 sentenece ，后面三列是必选的"""
    df = df[['sentenece', 'label', 'llm_res', 'reason']]
    return df


# 评估函数，需要根据不同数据自定义函数到 evals 模块
from evals.eval_emotion import eval_emotion
eval_fun = eval_emotion
