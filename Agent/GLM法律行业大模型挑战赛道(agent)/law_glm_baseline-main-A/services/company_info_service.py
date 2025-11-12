import json
from apis import (
    get_company_info,
    search_company_name_by_info,
)


def _get_full_name(company_name: str) -> str:
    """根据公司名称、公司简称或英文名称，获取该公司的全称。"""
    company_info_json = search_company_name_by_info(key="公司简称", value=company_name)
    if "公司名称" in company_info_json:
        company_name = company_info_json["公司名称"]
        return company_name
    company_info_json = search_company_name_by_info(key="英文名称", value=company_name)
    if "公司名称" in company_info_json:
        company_name = company_info_json["公司名称"]
        return company_name
    return company_name


def get_company_info_service(company_name: str) -> str:
    """
    根据公司名称，获得该公司所有基本信息。

    例如：
        输入：
        {"company_name": "广州发展集团股份有限公司"}
        输出：
        {'上市日期': '1997-07-18',
         '主营业务': '从事电力产业项目的设计、投资、工程总承包建设、生产、管理、销售。',
         '传真': '020-37850938',
         '入选指数': '国证Ａ指,巨潮小盘',
         '公司代码': '600098',
         '公司名称': '广州发展集团股份有限公司',
         '公司简称': '广州发展',
         '关联证券': None,
         '办公地址': '广东省广州市天河区临江大道3号31-32楼',
         '官方网址': 'www.gdg.com.cn',
         '总经理': None,
         '所属市场': '上交所',
         '所属行业': '电力、热力生产和供应业',
         '曾用简称': '广州控股',
         '机构简介': '公司前身系广州珠江电力工程公司，于1997年始进行股份制改组，以发起人净资产折为国家股56600万股，经1997年6月27日发行后，上市时总股本达66600万股，其内部职工股1000万股将于公众股9000万股1997年7月18日在上交所上市交易期满半后上市。',
         '每股面值': '1.0',
         '法人代表': '蔡瑞雄',
         '注册地址': '广东省广州市天河区临江大道3号发展中心30-32楼',
         '电子邮箱': '600098@gdg.com.cn',
         '经营范围': '从事能源（电力、煤炭、油品、天然气、新能源及可再生能源等综合能源业务）、节能、环保等业务的投资、管理，与上述业务有关的物资、设备、产品的销售（国家有专项专营规定的除外）。',
         '联系电话': '020-37850968',
         '英文名称': 'Guangzhou Development Group Incorporated',
         '董秘': '吴宏',
         '邮政编码': '510623',
         '首发主承销商': '广州证券有限责任公司',
         '首发价格': '7.87',
         '首发募资净额': '77250.0'}
    """
    company_name = _get_full_name(company_name)
    rsp = get_company_info(company_name)
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def count_company_by_industry_service(industry_name: str) -> str:
    """
    根据所属行业，统计该行业下公司的数量。

    例如：
        输入：
        {"industry_name": "批发业"}
        输出：
        {"所属行业": "批发业", "公司数量": 10}
    """
    company_list = search_company_name_by_info(key="所属行业", value=industry_name)
    if isinstance(company_list, dict):
        companies_number = 1
    elif isinstance(company_list, list):
        companies_number = len(company_list)
    else:
        companies_number = 0
    ret = {"所属行业": industry_name, "公司数量": companies_number}
    json_str = json.dumps(ret, ensure_ascii=False)
    return json_str


def search_company_name_by_info_service(key: str, value: str) -> str:
    """
    根据公司基本信息某个字段是某个值来查询具体的公司名称。
    可以输入的字段有['上市日期','主营业务','传真','入选指数',
    '公司代码','公司简称','关联证券','办公地址','官方网址',
    '总经理','所属市场','所属行业','曾用简称','机构简介',
    '每股面值','法人代表','注册地址','电子邮箱','经营范围',
    '联系电话','英文名称','董秘','邮政编码','首发主承销商',
    '首发价格','首发募资净额',]

    例如：
        输入：
        {
            "key": "所属行业",
            "value": "批发业"
        }
        输出：
        [{'公司名称': '国药集团药业股份有限公司'},
         {'公司名称': '苏美达股份有限公司'},
         {'公司名称': '深圳市英唐智能控制股份有限公司'}]
    """
    rsp = search_company_name_by_info(key, value)
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str
