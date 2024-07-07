# 项目介绍
使用 langchain 结合大模型的能力，识别句子中的实体。

# 数据
实体识别/data/question/初赛 B 榜question.json
识别 question 中的实体

# 代码
extract_entity 文件下的 run_extract_entity.py 为运行代码。
使用大模型为智谱，修改 llm 文件下的 glm_llm.py 中的 ZHIPUAI_API_KEY 即可。
具体识别逻辑，在 extract_entity.py 中。

