# 项目案例介绍
此仓库为 langchain 框架的案例，主要是做一些 prompt 工程的案例。

## 项目
每个项目都有 readme 介绍，可以参考
* **prompt自动优化**<br>
    使用智谱 glm4-airx 模型，构造 prompt 自动优化项目。经过测试，可以提高 prompt 优化的效率，提升准确率。不同场景需要测试。


* **GLM法律行业大模型挑战赛道(agent)**<br>
    使用 langchain 构建 agent，法律行业的应用，是阿里天池的一个比赛来着，作为学习 agent 的应用，是一个不错的案例。


* **langchain中的agent使用**<br>
    主要把 langchin 中几种 agent 进行实验，把支持的 agent 汇总到一起了，以及一些使用场景写在注释了。


* **专业识别**<br>
    langchian 的 rag 实现，从多个专业中，检索召回相关的后，再传给大模型去选择，主要使用的是 qwen 系列。


* **句子语义相似识别**<br>
    langchain 批次调用技术，使用 qwen 系列的模型，可以识别句子的相似度。


* **实体识别**<br>
    使用 langchin 结合大模型进行实体命名识别案例。


* **智能问答系统(Agent+RAG)**<br>
    阿里天池的练习来着，主要是 agent 与 rag 的应用，使用 glm4 结合 langchain 框架进行实操，作为学习案例可以。

* **智能问答系统(Agent+RAG)-1**<br>
    与上面同个项目，不过是自己实现 agent，plane agent，action agent，计划执行，虽然更灵活，可以自定义方式，但更耗费 token 了。
    两个方案共同难点是，生成的 sql 到底准不准，两个方案最终效果差不多的。

* **电影评论检索**<br>
    使用 glm4 通过 prompt 去检索数据，让模型能找到准确的数据。


* **评论情感识别**<br>
    使用 qwen 系列识别文本情感。


* **PDF文件理解**<br>
    测试 glm4-long 模型，长上下文理解的能力。 pdf 的字数为 11w，传进去解析到回答问题，用了 31s，效果还是不错的。 解析读取 pdf，调用大模型都是使用 langchain。

* **《斗破苍穹》RAG智搜/**<br>
    对比测试智谱 GLM 系列模型在小说问答 RAG 上的效果，进行多组实验，模型选择，分块方法，检索，及问题设置，总结普通 RAG 的局限性。

# model
存放 embedding 模型，可以自己去 huggingFace 下载


# 资料
一些 prompt 资料学习参考


# key.env
调用大模型的 api 存放文件，需要自己创建放在此根目录下，里面内容格式：<br>
```
DASHSCOPE_API_KEY=xxxxxx
QIANFAN_AK=xxxxxxxxxx
QIANFAN_SK=xxxxxxxxxx
```


# langchain_load_llm,py
langchain 加载大模型，langchian 支持的各大主流模型都可以在这里添加，也可以加载本地下载好的大模型到 langchain 中


# langchain_model.py
langchain 几大模块的的使用，相当于工具包，已封装了大部分，prompt，chain，RAG，Tool，Agent ，可以按需使用添加


# langchain smith
一个可以搜索 prompt 的地方，像 github 一样的 prompt 仓库
https://smith.langchain.com/hub?organizationId=eb05421f-4461-5f07-b32d-de9625dc0fac
