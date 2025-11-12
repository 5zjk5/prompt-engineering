# coding:utf8
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm.glm_llm import zhipu_glm_4


glm = zhipu_glm_4()
template = """
# 角色设定
你是法律行业的专家，擅长对用户的咨询的法律相关问题进行分类。

# 任务
用户会提供一个法律问题，你需要拆解问题，一步一步推理，判断依次需要哪些信息才能回答用户的问题，可以选择多个类别。

# 类别
Company：需要查询公司相关信息，如工商信息，注册信息等，以及限制高消费企业相关的可以归为此类。
Legal Instrument：需要根据案号，关联公司查询相关信息，如被告，原告，限制高消费，案件摘要等，可以归为此类。
Court：需要根据法院名称，法院代字查询法院相关数据，如法院网址，法院负责人等，可以归为此类。
Law Firms：需要根据律师事务所查询相关信息的，如服务已上市公司数量，律所负责人等，可以归为此类。
Address and Weather：地址，省市区以及天气相关的可以归为此类。

# 参考样例
- 样例1："爱玛科技集团股份有限公司涉案金额最高的法院的负责人是？"回答这个问题需要查询公司信息，公司名称为"爱玛科技集团股份有限公司"，查询公司信息，然后查询公司对应的法院，然后查询法院负责人。
所以选择`Company`、`Court`。
- 样例2："(2019)内民终564号案件的被告律师事务所地址在什么地方"回答这个问题需要查询案号为"(2019)内民终564号"的法律文件，获得被告律师事务，再查询律师事务所的地址。
所以选择`Legal Instrument`、`Law Firms`、`Address and Weather`。
。

# 问题
```{question}```

# 输出
按照以下格式输出：
```
推理过程:
分类结果:
```
"""

router_chain = (
        PromptTemplate.from_template(template)
        | glm
        | StrOutputParser()
)
