# coding:utf8
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain_core.output_parsers import JsonOutputParser


def str_chain(query, prompt, llm):
    """输出格式为字符串的链"""
    chain = (
            PromptTemplate.from_template(prompt)
            | llm
            | StrOutputParser()
    )
    res = chain.invoke({"question": query})
    return res


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


def batch_base_llm_chain(model, prompt, max_concurrency=5, **kwargs):
    """
    https://python.langchain.com/docs/modules/model_io/prompts/composition/#string-prompt-composition
    基础链，带有变量的 prompt ，model 两个组成链，批次调用
    :param model: llm
    :param prompt: prompt 其中的变量是用 {} 括起来的
    :param kwargs: prompt 中的变量
    :param max_concurrency: 并发请求数
    e.g:
        promt = 'tell me a joke about {other} and {topic2}'
        other = ['bear', 'dog']
        topic2 = ['cat', 'monkey']

        传进来后的 kwargs: kwargs = {'topic1': ['bear', 'dog'], 'topic2': ['cat', 'monkey']}
        处理后 batch_list: batch_list = [{"topic1": "bears", "topic2": "cat"}, {"topic1": "dog", "topic2": "monkey"}]
    :return:
    """
    prompt = PromptTemplate.from_template(prompt)
    chain = LLMChain(llm=model, prompt=prompt)

    # 确保所有列表长度相同，构造批次列表
    keys = list(kwargs.keys())
    first_list_length = len(kwargs[keys[0]])
    if all(len(kwargs[key]) == first_list_length for key in keys):
        # 使用zip函数将所有值配对
        paired_values = zip(*[kwargs[key] for key in keys])
        # 遍历配对后的值，构造新的字典列表
        batch_list = [dict(zip(keys, values)) for values in paired_values]
    else:
        print("批次对应列表长度不一致，无法转换。")
        return None

    res = chain.batch(batch_list, config={"max_concurrency": max_concurrency})
    return res


def csv_parser_chain(prompt_string, model, **kwargs):
    """
    https://python.langchain.com/docs/modules/model_io/output_parsers/types/csv/
    列表格式
    :param prompt_string: prompt 字符串，里面变量使用 {} 括起来
    :param model: llm
    :param kwargs: 字典变量
    :return:
    """
    output_parser = CommaSeparatedListOutputParser()
    format_instructions = output_parser.get_format_instructions()
    kwargs['format_instructions'] = format_instructions  # 格式化输出设置
    prompt = PromptTemplate(
        template=prompt_string + "\n{format_instructions}",
        input_variables=[],
        partial_variables=kwargs,  # 变量赋值
    )
    chain = prompt | model | output_parser
    res = chain.invoke({})
    return res


def json_parser_chain(prompt_string, model, json_class=None, **kwargs):
    """
    https://python.langchain.com/docs/modules/model_io/output_parsers/types/json/
    json
    :param prompt_string: prompt 字符串，里面变量是已经填充好的
    :param model: llm
    :param enum_class: json 类，用来指定输出字典的键，也可以不用指定，这样默认就一个键
            from langchain_core.pydantic_v1 import BaseModel, Field
       e.g  class Joke(BaseModel):
                setup: str = Field(description="question to set up a joke")
                punchline: str = Field(description="answer to resolve the joke")
    :param kwargs: 字典变量
    :return:
    """
    parser = JsonOutputParser(pydantic_object=json_class)
    format_instructions = parser.get_format_instructions()
    kwargs['format_instructions'] = format_instructions  # 格式化输出设置
    kwargs['prompt_string'] = prompt_string
    prompt = PromptTemplate(
        template="Answer the user query.\n{format_instructions}\n{prompt_string}\n",
        input_variables=[],
        partial_variables=kwargs,  # 设置所有变量
    )
    chain = prompt | model | parser
    res = chain.invoke({})
    return res
