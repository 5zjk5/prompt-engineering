# coding:utf8
import os
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv(r'D:\Python_project\NLP\大模型学习\prompt-engineering\key.env')
ZHIPUAI_API_KEY = os.getenv('ZHIPUAI_API_KEY')


def zhipu_glm_4_long(temperature=0.9):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4-long",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def pdf_loader(filepath, extract_images=True, is_directory=False):
    """
    https://python.langchain.com/docs/modules/data_connection/document_loaders/pdf/
    加载 pdf，默认 page 是页码，但可能多出几页
    :param filepath:
    :param extract_images: 默认提取图片文字，是否提取 pdf 中的图片的文字
    :param is_directory: 如果传入进来是目录，加载此路径下的所有 pdf，但图片中的文字不能识别
    :return:
    """
    if is_directory:
        filepath = is_directory
        loader = PyPDFDirectoryLoader(filepath)
        docs = loader.load()
        return docs
    else:
        if extract_images:
            loader = PyPDFLoader(filepath, extract_images=extract_images)
        else:
            loader = PyMuPDFLoader(filepath)  # 最快的 PDF 解析选项，但不能提取图片中的文字
        pages = loader.load_and_split()
        return pages


def base_llm_chain(model, prompt, **kwargs):
    """
    https://python.langchain.com/docs/modules/model_io/prompts/composition/#string-prompt-composition
    基础链，带有变量的 prompt ，model 两个组成链
    :param model: llm
    :param prompt: prompt 其中的变量是用 {} 括起来的
    :param kwargs: prompt 中的变量
    :return:
    """
    prompt = PromptTemplate.from_template(prompt)
    chain = LLMChain(llm=model, prompt=prompt)
    res = chain.run(kwargs)
    return res


if __name__ == '__main__':
    start = time.time()

    filepath = 'data/纳瓦尔宝典.pdf'
    pages = pdf_loader(filepath, extract_images=False)
    pages = [page.page_content for page in pages]

    llm = zhipu_glm_4_long(temperature=0.9)

    prompt = f"""
给你提供 PDF 的电子书内容，你需要认真阅读理解每一页，理解整体电子书的文章核心观点，并回答问题，以下是电子书的每一页:
```
{pages}
```
----------------------------------------------------------
问题：总结出来尽可能多的这本书推荐的越多越好日常行为原则以及使用场景。
    """

    response = base_llm_chain(llm, prompt)
    print(response)

    end = time.time()
    print(f"{end - start}")
