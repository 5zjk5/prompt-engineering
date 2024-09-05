# coding:utf8
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain


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
