# coding:utf8
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback


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
    with get_openai_callback() as cb:
        res = chain.invoke(kwargs)
        input_prompt = prompt.template.format(**kwargs)
        print(f'输入 token：{cb.completion_tokens}/输出 token：{cb.prompt_tokens}/总共 token：{cb.total_tokens}/')
        # print(f'输入 prompt：\n{input_prompt}')
        return res['text']
