# 项目介绍
利用智谱 glm4-airx 模型，构造 prompt 自动优化项目。

项目使用 langchain 框架，调用 prompt 链，使用 langchain 的批次调用技术，加快速度。

自动优化主要适用于 prompt 有些通用性，但是参数化部分需要根据不同的数据进行优化的情况。

不一定对所有数据都适用，需要根据实际场景进行测试。


# 效果展示
## 示例1
使用 data/input_data/similary.csv 数据测试，他是一个判断两个句子是否相似的数据集。

取用前 100 条数据，初始 prompt 如下：
```js
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
```
准确率：80-81%，有一定浮动。

使用自动优化后，连续跑了几次，温度设为 0.1，提升 3-4% 准确率.

日志在 data/output_data/similary-3个错误样本/output.log
```js
第 1 轮，当前准确率：80.0
第 2 轮，当前准确率：82.0
第 3 轮，当前准确率：83.0
```

日志在 data/output_data/similary-1个错误样本/output.log
```js
第 1 轮，当前准确率：81.0
第 2 轮，当前准确率：84.0
第 3 轮，当前准确率：85.0
```

优化过 prompt 样例“
```js
**标题：**句子语义相似度评估

**目的：**判断两个句子，sentence1 和 sentence2，是否在语义上相同或非常相似。

**指导说明：**
- 细致分析sentence1和sentence2的语义内容。
- 结合句子的整体含义、上下文和传达的意图进行综合判断。
- 当两个句子在核心含义、情感表达或意图上一致时，即使表述方式不同，也应输出1。
- 当两个句子在含义、情感或意图上存在显著差异时，即使表述存在表面相似性，也应输出0。
- 仅输出数字1或0作为判断结果，避免提供额外解释或信息。

**示例格式：**
输入：
Sentence1: 今天天气真好，适合出去散步。
Sentence2: 今天阳光明媚，是个散步的好日子。
输出：1

输入：
Sentence1: 请问这里离最近的地铁站有多远？
Sentence2: 这附近有公交站吗？
输出：0

轮到你了：
输入：
Sentence1: {sentence1}
Sentence2: {sentence2}

输出：
输入：
Sentence1: {sentence1} 
Sentence2: {sentence2}
，
```

## 示例2
使用 data/input_data/emotion.csv 数据测试，他是一个判断情感积极，消极的数据集。

取用前 100 条数据，初始 prompt 如下：
```js
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
```
准确率：96%

已经很高了，智谱在文本情感上表现非常好。

优化后的提示词：
```js
请根据以下评论内容判断其情感倾向：
- 文本：{sentence}
- 判断：{Positive/Negative}


优化后的决策规则：
1. 检查评论中是否存在积极或消极情感关键词，如“点赞”、“质量靠谱”、“满意”为积极关键词，“不满”、“不舒服”、“效果一般”为消极关键词。
2. 分析评论的整体语境，考虑情感关键词出现的频率和上下文。
3. 判断评论者对商品的整体满意度，注意具体抱怨或不满的细节。
4. 如果评论中积极情感关键词显著多于消极关键词，且整体语境正面，输出`Positive`。
5. 如果评论中消极情感关键词显著多于积极关键词，或存在明显的抱怨和不满，输出`Negative`。
6. 如果评论中的情感关键词不明显，或整体语境难以判断，进一步分析评论细节，寻找情感倾向的线索，根据综合判断输出`Positive`或`Negative`。
```

进行了三轮，已经很难提升了，基本没变化，data/output_data/emotion/output.log：
```js
第 1 轮，当前准确率：96.0
第 2 轮，当前准确率：95.0
第 3 轮，当前准确率：96.0
```

# 项目结构
run_main.py 为主入口，主要流程都有注释。
## 配置文件
config/config.py 为配置文件不同任务需要不同配置，主要配置可参考样例 config/config_similary.py.

每个配置都有注释。

## prompt 模版
prompt 不同模型，不同任务会有不同表现，可以需要根据实际需求进行优化。

prompt 配置文件 config/prompt.py

模版为 config/prompt_silimary.py config/prompt_emotion.py 

## 评估脚本
evals 文件夹下，由于每个任务可能数据不同，评估方式也不同，需要自己编写后写在配置文件中，参考样例。







