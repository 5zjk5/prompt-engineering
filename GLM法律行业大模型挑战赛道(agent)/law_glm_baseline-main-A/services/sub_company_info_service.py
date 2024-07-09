import json

from apis import (
    get_listed_company_info,
    search_company_name_by_super_info,
    search_company_name_by_info
)
from utils import convert_to_float, convert_to_str


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
    company_info_json = search_company_name_by_info(key="曾用简称", value=company_name)
    if "公司名称" in company_info_json:
        company_name = company_info_json["公司名称"]
        return company_name
    return company_name


def get_parent_company_info_service(company_name: str) -> str:
    """
    根据子公司的公司名称，查询该公司的母公司信息，或者说查询该公司是哪家公司旗下的子公司。
    母公司信息包括'母公司名称'、'母公司参股比例'、'母公司投资金额'。
    """
    company_name = _get_full_name(company_name)
    rsp = get_listed_company_info(company_name)
    ret = {
        "公司名称": company_name
    }
    if "关联上市公司全称" in rsp:
        ret["母公司名称"] = rsp["关联上市公司全称"]
    if "上市公司参股比例" in rsp:
        ret["母公司参股比例"] = rsp["上市公司参股比例"]
    if "关联上市公司全称" in rsp:
        ret["母公司投资金额"] = rsp["上市公司投资金额"]
    json_str = json.dumps(ret, ensure_ascii=False)
    return json_str


def get_sub_company_name_service(company_name: str) -> str:
    """
    根据母公司的公司名称，获得该公司旗下的所有子公司的名称。
    """
    company_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", company_name)
    for item in rsp:
        sub_company_name = item["公司名称"]
        del item["公司名称"]
        item["子公司名称"] = sub_company_name
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def get_sub_company_info_service(company_name: str) -> str:
    """
    根据母公司的公司名称，获得该公司的所有子公司、投资对象的信息。
    包括'上市公司关系'、'上市公司参股比例'、'上市公司投资金额'、'公司名称'、'关联上市公司全称'，
    值得注意的是关联上市公司是该公司的名称，公司名称是该公司的子公司的名称。
    """
    company_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", company_name)
    sub_company_name_list = [item["公司名称"] for item in rsp]
    listed_company_info_list = []
    for i in range(0, len(sub_company_name_list), 100):
        batch_list = sub_company_name_list[i:i + 100]
        listed_company_info_list.extend(get_listed_company_info(batch_list))
    for listed_company_info in listed_company_info_list:
        del listed_company_info["关联上市公司股票代码"]
        del listed_company_info["关联上市公司股票简称"]
    json_str = json.dumps(listed_company_info_list, ensure_ascii=False)
    return json_str


def count_sub_company_service(company_name: str) -> str:
    """
    根据母公司的公司名称，统计该公司所有子公司的数量。
    """
    company_name = _get_full_name(company_name)
    all_sub_company_name = search_company_name_by_super_info("关联上市公司全称", company_name)
    ret = {
        "公司名称": company_name,
        f"{company_name}所有子公司的数量": len(all_sub_company_name)
    }
    json_str = json.dumps(ret, ensure_ascii=False)
    return json_str


def search_company_name_by_super_info_service(key: str, value: str) -> str:
    """
    根据关联上市公司信息某个字段是某个值来查询具体的公司名称。
    可以输入的字段有['上市公司关系','上市公司参股比例','上市公司投资金额','关联上市公司全称',
    '关联上市公司股票代码','关联上市公司股票简称',]

    例如：
        输入：
        {"key": "关联上市公司全称",
         "value": "冠昊生物科技股份有限公司"}
        输出：
        [{'公司名称': '北昊干细胞与再生医学研究院有限公司'},
         {'公司名称': '北京申佑医学研究有限公司'},
         {'公司名称': '北京文丰天济医药科技有限公司'},
         {'公司名称': '冠昊生命健康科技园有限公司'}]
    """
    rsp = search_company_name_by_super_info(key, value)
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def query_total_amount_invested_in_subsidiaries(company_name: str) -> str:
    """根据上市公司的公司名称、公司简称或英文名称，查询该公司在子公司投资的总金额。"""
    full_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", full_name)
    total_amount = 0
    for item in rsp:
        sub_company_name = item["公司名称"]
        listed_company_info = get_listed_company_info(sub_company_name)
        if "上市公司投资金额" not in listed_company_info:
            continue
        amount = listed_company_info["上市公司投资金额"]
        if amount is None:
            continue
        total_amount += convert_to_float(amount)
    rsp = {
        "公司名称": company_name,
        "在子公司投资的总金额": convert_to_str(total_amount)
    }
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def query_total_amount_fully_owned(company_name: str) -> str:
    """根据上市公司的公司名称、公司简称或英文名称，查询该公司全资控股的子公司有多少家"""
    full_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", full_name)
    total_amount = 0
    sub_company_name_list = []
    for item in rsp:
        sub_company_name = item["公司名称"]
        listed_company_info = get_listed_company_info(sub_company_name)
        if "上市公司参股比例" not in listed_company_info:
            continue
        investment_proportion = listed_company_info["上市公司参股比例"]
        if investment_proportion is None:
            continue
        if int(float(investment_proportion)) == 100:
            sub_company_name_list.append(sub_company_name)
            total_amount += 1
    rsp = {
        "公司名称": company_name,
        "全资控股的子公司数量": total_amount,
        "全资控股的子公司名称": sub_company_name_list
    }
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def query_total_amount_half_owned_investment(company_name: str) -> str:
    """根据上市公司的公司名称、公司简称或英文名称，查询该公司投资超5000万并控股超50%的子公司有多少家"""
    full_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", full_name)
    total_amount = 0
    sub_company_name_list = []
    for item in rsp:
        sub_company_name = item["公司名称"]
        listed_company_info = get_listed_company_info(sub_company_name)
        if "上市公司参股比例" not in listed_company_info:
            continue
        if "上市公司投资金额" not in listed_company_info:
            continue
        investment_proportion = listed_company_info["上市公司参股比例"]
        investment_amount = listed_company_info["上市公司投资金额"]
        if investment_proportion is None:
            continue
        if investment_amount is None:
            continue
        if investment_amount.endswith("亿"):
            investment_amount = investment_amount[:-1]
            investment_amount = float(investment_amount) * 10000
        else:
            investment_amount = float(investment_amount[:-1])
        if int(float(investment_proportion)) > 50 and int(investment_amount) > 5000:
            sub_company_name_list.append(sub_company_name)
            total_amount += 1
    rsp = {
        "公司名称": company_name,
        "投资超5000万并控股超50%的子公司数量": total_amount,
        "投资超5000万并控股超50%的子公司名称": sub_company_name_list
    }
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str


def query_total_amount_half_owned(company_name: str) -> str:
    """根据上市公司的公司名称、公司简称或英文名称，查询该公司控股超过50%(控股)的子公司数量，"""
    full_name = _get_full_name(company_name)
    rsp = search_company_name_by_super_info("关联上市公司全称", full_name)
    total_amount = 0
    for item in rsp:
        sub_company_name = item["公司名称"]
        listed_company_info = get_listed_company_info(sub_company_name)
        if "上市公司参股比例" not in listed_company_info:
            continue
        if "上市公司投资金额" not in listed_company_info:
            continue
        investment_proportion = listed_company_info["上市公司参股比例"]
        if investment_proportion is None:
            continue
        if int(float(investment_proportion)) > 50:
            total_amount += 1
    rsp = {
        "公司名称": company_name,
        "控股超50%的子公司": total_amount
    }
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str
