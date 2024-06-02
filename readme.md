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
