# coding:utf8
from llm.glm_llm import zhipu_glm_4
from langchain.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.chains import LLMChain
import copy


llm = zhipu_glm_4()

# 定义实体字段
# 类型：list, string, number
response_schemas = [
    # company
    ResponseSchema(type='list', name='company', description='公司名称，如果不能提取返回 []'),
    ResponseSchema(type='list', name='company_abbreviation', description='公司简称，如果不能提取返回 []'),
    ResponseSchema(type='list', name='company_code', description='公司代码，如果不能提取返回 []'),
    ResponseSchema(type='list', name='social_credit_code', description='统一社会信用代码，例如：91310000677833266F，如果不能提取返回 []'),
    ResponseSchema(type='list', name='affiliated_listed_company', description='关联上市公司，如果不能提取返回 []'),
    ResponseSchema(type='list', name='high_consumption_company', description='限制高消费企业名称，如果不能提取返回 []'),

    # address weateher
    ResponseSchema(type='list', name='address', description='地址，如果不能提取返回 []'),
    ResponseSchema(type='list', name='province', description='省份，如果不能提取返回 []'),
    ResponseSchema(type='list', name='city', description='城市，如果不能提取返回 []'),
    ResponseSchema(type='list', name='distinct', description='区县，如果不能提取返回 []'),
    ResponseSchema(type='list', name='date', description='日期，日期格式例如：2020年1月1日，如果不能提取返回 []'),

    # court
    ResponseSchema(type='list', name='court_name', description='法院名称，如果不能提取返回 []'),
    ResponseSchema(type='list', name='court_daizi', description='法院代字，例如：沪0115，如果不能提取返回 []'),

    # law firm
    ResponseSchema(type='list', name='lawfirm_name', description='律师事务所名称，如果不能提取返回 []'),

    # legal instrument
    ResponseSchema(type='list', name='legal_document_code', description='案号，例如：(2019)沪0115民初61975号，如果不能提取返回 []'),
    ResponseSchema(type='list', name='affiliated_company', description='关联公司，如果不能提取返回 []'),
]

def structured_output_parser(response_schemas):
    text = '''
    请从以下文本中，抽取出实体信息，并按json格式返回，json包含首尾的 "```json" 和 "```":
    以下是字段含义和类型，要求保留所有字段，且字段对应的值必须是列表格式，如果提取不到，也需要保留为 []：
    '''
    for schema in response_schemas:
        text += schema.name + ' 字段，表示：' + schema.description + '，类型为：' + schema.type + '\n'
    return text


def is_not_none(output):
    """提取结果，过滤为空的"""
    tmp_output = copy.deepcopy(output)
    for key, value in output.items():
        if not value:
            del tmp_output[key]
    return tmp_output


def key_map(outputs):
    """字典映射，把键的值改为中文的"""
    key_map_dict = {
        'company': '公司名称',
        'company_abbreviation': '公司简称',
        'company_code': '公司代码',
        'social_credit_code': '统一社会信用代码',
        'affiliated_listed_company': '关联上市公司',
        'high_consumption_company': '限制高消费企业名称',
        'address': '地址',
        'province': '省份',
        'city': '城市',
        'distinct': 'date',
        'court_name': '法院名称',
        'court_daizi': '法院代字',
        'lawfirm_name': '律师事务所名称',
        'legal_document_code': '案号',
        'affiliated_company': '关联公司'
    }
    tmp_outputs = {}
    for key, value in outputs.items():
        tmp_outputs[key_map_dict.get(key)] = value
    return tmp_outputs


def extract_entity(question, llm=llm):
    """实体提取"""
    outputs = {}
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = structured_output_parser(response_schemas)
    template = '''
        1、从以下用户输入的句子中，提取实体内容。
        2、仅根据用户输入抽取，不要推理。
        3、注意json格式，在json中不要出现//
        {format_instructions}
        用户输入：{input}
        输出：
        '''
    prompt = PromptTemplate(
        template=template,
        partial_variables={'format_instructions': format_instructions},
        input_variables=['input']
    )
    chain = LLMChain(
        llm=llm,
        prompt=prompt
    )
    # llm_output = chain.run(input='感冒是一种什么病？会导致咳嗽吗？')
    llm_output = chain.invoke({'input': question})['text']
    output = output_parser.parse(llm_output)
    output = is_not_none(output)
    outputs.update(output)

    outputs = key_map(outputs)
    return outputs


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