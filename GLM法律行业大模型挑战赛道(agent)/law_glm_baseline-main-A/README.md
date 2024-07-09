# law_agent

> 第三届琶洲算法大赛-GLM法律行业大模型挑战赛道

## 赛题描述

> 欢迎参加「GLM 法律行业大模型挑战赛」。
> 
> 随着技术的进步，大语言模型（LLM）已经在多个领域展现出显著成效，法律行业也不例外。LLM 在法律服务、案件分析和合同审核等方面已显示出其强大潜力。
> 
> 为探索 LLM 在法律行业的应用潜力，我们在琶洲算法大赛主办方的指导下，推出了 GLM 法律行业大模型挑战赛。
> 
> 赛题由智谱AI、深圳数据交易所、安硕信息和魔搭社区、天池平台联合承办，比赛旨在推动大模型在法律领域的发展，并邀请广大开发者和技术团队参与创新。
> 
> 参赛者需基于 GLM-4 模型，制定技术方案。方案应利用大语言模型的语义理解和函数调用功能，准确解析用户查询，并通过访问相关法律数据库或 API，提供服务，包括解答法律问题、查询案件信息、检索历史案件和分析司法数据。

## 环境搭建

```shell
conda create -n law python=3.10
conda activate law
pip install -r requirements.txt
```

## 数据说明

> 本赛题的数据集来源于随机选取的上市公司名单。数据集包含这些公司的基础信息、工商信息、关联子公司信息，以及裁判文书信息。此外，还包括专业的法律场景数据，如文书模板、法律条文、评估报告等。
> 
> 数据集中，您可以了解到公司的全称、简称、所属行业、成立日期等基本信息，以及注册状态、注册资本、省份等注册信息。同时，数据集提供了子公司与上市公司的关联信息，包括参股比例和投资金额。法律文件的相关信息，如案号、原告被告和判决结果等也被记录在内。这些数据帮助您全面了解公司的运营和法律风险状况。
> 
> 本次比赛提供的数据查询API主要提供来自四个数据表的数据查询，分别包括公司基本信息表，公司注册信息表，上市公司子公司关联信息表，法律文书信息表。选手需要灵活调用API来回答问题，在调用API时需要传入手机号进行报名验证，调用信息将会被记录，以防止非正常调用&作弊等。

### 数据表schema

```python
class CompanyInfo(Base):
    __tablename__ = "company_info"
    公司名称 = Column(Text, primary_key=True)
    公司简称 = Column(Text)
    英文名称 = Column(Text)
    关联证券 = Column(Text)
    公司代码 = Column(Text)
    曾用简称 = Column(Text)
    所属市场 = Column(Text)
    所属行业 = Column(Text)
    上市日期 = Column(Text)
    法人代表 = Column(Text)
    总经理 = Column(Text)
    董秘 = Column(Text)
    邮政编码 = Column(Text)
    注册地址 = Column(Text)
    办公地址 = Column(Text)
    联系电话 = Column(Text)
    传真 = Column(Text)
    官方网址 = Column(Text)
    电子邮箱 = Column(Text)
    入选指数 = Column(Text)
    主营业务 = Column(Text)
    经营范围 = Column(Text)
    机构简介 = Column(Text)
    每股面值 = Column(Text)
    首发价格 = Column(Text)
    首发募资净额 = Column(Text)
    首发主承销商 = Column(Text)

class CompanyRegister(Base):
    __tablename__ = 'company_register'
    公司名称 = Column(Text, primary_key=True, default='')
    登记状态 = Column(Text, default='')
    统一社会信用代码 = Column(Text, default='')
    注册资本 = Column(Text, default='') # 单位：万元
    成立日期 = Column(Text, default='')
    省份 = Column(Text, default='')
    城市 = Column(Text, default='')
    区县 = Column(Text, default='')
    注册号 = Column(Text, default='')
    组织机构代码 = Column(Text, default='')
    参保人数 = Column(Text, default='')
    企业类型 = Column(Text, default='')
    曾用名 = Column(Text, default='')

class SubCompanyInfo(Base):
    __tablename__ = 'sub_company_info'
    关联上市公司股票代码 = Column(Text, default='')
    关联上市公司股票简称 = Column(Text, default='')
    关联上市公司全称 = Column(Text, default='')
    上市公司关系 = Column(Text, default='')
    上市公司参股比例 = Column(Text, default='')
    上市公司投资金额 = Column(Text, default='')
    公司名称 = Column(Text, primary_key=True, default='')
    
class LegalDocument(Base):
    __tablename__ = 'legal_document'
    标题 = Column(Text, default='')
    案号 = Column(Text, default='', primary_key=True)
    文书类型 = Column(Text, default='')
    原告 = Column(Text, default='')
    被告 = Column(Text, default='')
    原告律师 = Column(Text, default='')
    被告律师 = Column(Text, default='')
    案由 = Column(Text, default='')
    审理法条依据 = Column(Text, default='')
    涉案金额 = Column(Text, default='')
    判决结果 = Column(Text, default='')
    胜诉方 = Column(Text, default='')
    文件名 = Column(Text, default='')
```

### API列表

鉴权token（暂定为手机号）都需要在header里体现


| API序号 | API描述                       | 路由                                         | 输入参数                | 返回值              |
|-------|-----------------------------|--------------------------------------------|---------------------|------------------|
| 0     | 根据公司名称获得该公司所有基本信息           | /law_api/get_company_info                  | company_name: str   | ALL_COMPANY_INF  |
| 1     | 根据公司基本信息某个字段是某个值来查询具体的公司名称  | /law_api/search_company_name_by_info       | key: str value: str | 公司名称: str        |
| 2     | 根据公司名称获得该公司所有注册信息           | /law_api/get_company_register              | company_name: str   | COMPANY_REGISTER |
| 3     | 根据公司注册信息某个字段是某个值来查询具体的公司名称  | /law_api/search_company_name_by_register   | key: str value: str | 公司名称: str        |
| 4     | 根据公司名称获得该公司所有关联子公司信息        | /law_api/get_sub_company_info              | company_name: str   | SUB_COMPANY_INFO |
| 5     | 根据关联子公司信息某个字段是某个值来查询具体的公司名称 | /law_api/search_company_name_by_sub_info   | key: str value: str | 公司名称: str        |
| 6     | 根据案号获得该案所有基本信息              | /law_api/get_legal_document                | case_num: str       | LEGAL_DOCUMENT   |
| 7     | 根据法律文书某个字段是某个值来查询具体的案号      | /law_api/search_case_num_by_legal_document | key: str value: str | 案号: str          |

## 示例

### Python调用API示例

**根据主键查询所有信息**

```python
import apis

domain = ""  # 暂未公开
url = f"https://{domain}/law_api/get_company_register"

headers = {
    'Content-Type': 'application/json'
}

data = {
    "company_name": "广州发展集团股份有限公司"
}

rsp = apis.post(url, json=data, headers=headers)
print(rsp.json())
```

**输出**

>{'公司名称': '广州发展集团股份有限公司', '登记状态': '在业', '统一社会信用代码': '91440101231243173M', '注册资本': '354405.5525', '成立日期': '1992-11-13', '省份': '广东省', '城市': '广州
市', '区县': '天河区', '注册号': '440101000196724', '组织机构代码': '23124317-3', '参保人数': '207.0', '企业类型': '股份有限公司（上市、国有控股）', '曾用名': '广州发展实业控股集团股份有 
限公司、广州电力企业集团股份有限公司、广州珠江电力工程公司、广州电力企业集团有限公司'}

**根据某个值查询公司名称**

```python
import apis

domain = ""  # 暂未公开
url = f"https://{domain}/law_api/search_company_name_by_register"

headers = {
    'Content-Type': 'application/json'
}

data = {
    "key": "统一社会信用代码",
    "value": "91440101231243173M"
}

rsp = apis.post(url, json=data, headers=headers)
print(rsp.json())
```

**输出**

> {'公司名称': '广州发展集团股份有限公司'}

### 获取函数调用

```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="") # 请填写您自己的APIKey

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_legal_person",
            "description": "根据提供的公司名称，查询该公司对应的法人代表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        }
    }
]
messages = [
    {
        "role": "user",
        "content": "我想要联系广州发展集团股份有限公司公司的法人代表，请问他的名字是什么？"
    }
]
response = client.chat.completions.create(
    model="glm-4", # 填写需要调用的模型名称
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
print(response.choices[0].message)
```

### 调用函数

```python
import json

function = response.choices[0].message.tool_calls.function
func_args = function.arguments
func_name = function.name

function = response.choices[0].message.tool_calls[0].function
func_args = function.arguments
func_name = function.name

url = f"http://{domain}/law_api/{func_name}"

headers = {
    'Content-Type': 'application/json'
}

rsp = requests.post(url, json=json.loads(func_args), headers=headers)
print(rsp.json())
```

### 生成答案

```python
messages = [
    {
        "role": "user",
        "content": "我想要联系广州发展集团股份有限公司公司的法人代表，请问他的名字是什么？"
    }
]
messages.append(response.choices[0].message.model_dump())
messages.append({
    "role": "tool",
    "content": f"{rsp.json()}",
    "tool_call_id": response.choices[0].message.tool_calls[0].id
})


print(client.chat.completions.create(
    model="glm-4",  # 填写需要调用的模型名称
    messages=messages,
    tools=tools,
).choices[0].message)
```

## 本 baseline 使用说明

1. 按照环境搭建，搭建环境。
2. 修改 ./apis/data_query_api.py 中的 TEAM_TOKEN
3. 修改 ./llm/glm_llm.py 中的 openai_api_key
4. 修改 answer.py 中输出文件的路径
5. 运行 answer.py