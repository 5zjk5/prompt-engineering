from typing import List, Union
import requests

DOMAIN = "comm.chatglm.cn"
TEAM_TOKEN = "5876A40D2FA07E3D4EF9E0B1E4CF99D4EAB2D2F190DB1352"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {TEAM_TOKEN}'
}


def get_company_info(company_name: Union[str, List[str]]) -> dict:
    """
    根据公司名称获得该公司所有基本信息。

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
    url = f"https://{DOMAIN}/law_api/get_company_info"
    data = {
        "company_name": company_name
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("get_company_info", data,rsp.json())
    return rsp.json()


def search_company_name_by_info(key: str, value: str) -> dict:
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
        {"key": "所属行业",
         "value": "批发业"}
        输出：
        [{'公司名称': '国药集团药业股份有限公司'},
         {'公司名称': '苏美达股份有限公司'},
         {'公司名称': '深圳市英唐智能控制股份有限公司'}]
    """
    url = f"https://{DOMAIN}/law_api/search_company_name_by_info"

    data = {
        "key": key,
        "value": value
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("search_company_name_by_info", data, rsp.json())
    return rsp.json()


def get_company_register(company_name: Union[str, List[str]]) -> dict:
    """
    根据公司名称获得该公司所有注册信息。

    例如：
        输入：
        {"company_name": "广州发展集团股份有限公司"}
        输出：
        {'企业类型': '股份有限公司（上市、国有控股）',
         '公司名称': '广州发展集团股份有限公司',
         '区县': '天河区',
         '参保人数': '207.0',
         '城市': '广州市',
         '成立日期': '1992-11-13',
         '曾用名': '广州发展实业控股集团股份有限公司、广州电力企业集团股份有限公司、广州珠江电力工程公司、广州电力企业集团有限公司',
         '注册号': '440101000196724',
         '注册资本': '354405.5525',
         '登记状态': '在业',
         '省份': '广东省',
         '组织机构代码': '23124317-3',
         '统一社会信用代码': '91440101231243173M'}
    """
    url = f"https://{DOMAIN}/law_api/get_company_register"

    data = {
        "company_name": company_name
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("get_company_register", data, rsp.json())
    return rsp.json()


def search_company_name_by_register(key: str, value: str) -> dict:
    """
    根据公司注册信息某个字段是某个值来查询具体的公司名称。
    可以输入的字段有['企业类型','区县','参保人数','城市',
    '成立日期','曾用名','注册号','注册资本','登记状态',
    '省份','组织机构代码','统一社会信用代码']

    例如：
        输入：
        {"key": "注册号",
         "value": "440101000196724"}
        输出：
        {"公司名称": "广州发展集团股份有限公司"}
    """
    url = f"https://{DOMAIN}/law_api/search_company_name_by_register"

    data = {
        "key": key,
        "value": value
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("search_company_name_by_register", data, rsp.json())
    return rsp.json()


def get_listed_company_info(company_name: Union[str, List[str]]) -> dict:
    """
    根据公司名称获得与该公司有关的所有关联上市公司信息。

    例如：
        输入：
        {"company_name": "广东天昊药业有限公司"}
        输出：
        {'上市公司关系': '子公司',
         '上市公司参股比例': '100.0',
         '上市公司投资金额': '7000.00万',
         '公司名称': '广东天昊药业有限公司',
         '关联上市公司全称': '冠昊生物科技股份有限公司',
         '关联上市公司股票代码': '300238',
         '关联上市公司股票简称': '冠昊生物'}
    """
    url = f"https://{DOMAIN}/law_api/get_sub_company_info"

    data = {
        "company_name": company_name
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("get_listed_company_info", data, rsp.json())
    return rsp.json()


def search_company_name_by_super_info(key: str, value: str) -> dict:
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
    url = f"https://{DOMAIN}/law_api/search_company_name_by_sub_info"

    data = {
        "key": key,
        "value": value
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("search_company_name_by_super_info", data, rsp.json())
    return rsp.json()


def get_legal_document(case_num: Union[str, List[str]]) -> dict:
    """
    根据案号获得该案所有基本信息。

    例如：
        输入：
        {"case_num": "(2020)赣0191民初1045号"}
        输出：
        {'判决结果': '一、南昌绿地申新置业有限公司于本判决生效之日起十五日内向上海澳辉照明电器有限公司支付本金1179104元。\n'
             '二、南昌绿地申新置业有限公司于本判决生效之日起十五日内向上海澳辉电器有限公司支付利息(以质保金1179104元为基数,按年利率6%,从2019年6月7日起计算至1179104元实际付清之日止)。\n'
             '三、驳回上海澳辉电器有限公司的其他诉讼请求。',
         '原告': '上海澳辉照明电器有限公司',
         '原告律师': '刘某某,北京大成(南昌)律师事务所律师\n罗某某,北京大成(南昌)律师事务所律师',
         '审理法条依据': '无',
         '文书类型': '民事判决书',
         '文件名': '（2020）赣0191民初1045号.txt',
         '标题': '上海澳辉照明电器有限公司与上海建工集团股份有限公司、南昌绿地申新置业有限公司合同纠纷一审民事判决书',
         '案号': '(2020)赣0191民初1045号',
         '案由': '合同纠纷',
         '涉案金额': '1179104',
         '胜诉方': '原告',
         '被告': '上海建工集团股份有限公司\n南昌绿地申新置业有限公司',
         '被告律师': '罗丽萍,公司员工\n李某某,江西豫章律师事务所律师\n蔡某某,江西豫章律师事务所实习律师'}
    """
    if isinstance(case_num, str):
        case_num = case_num.replace('（', '(').replace('）', ')')

    if isinstance(case_num, list):
        new_case_num = []
        for ele in case_num:
            new_case_num.append(ele.replace('（', '(').replace('）', ')'))
        case_num = new_case_num

    url = f"https://{DOMAIN}/law_api/get_legal_document"

    data = {
        "case_num": case_num
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("get_legal_document", data, rsp.json())
    return rsp.json()


def search_case_num_by_legal_document(key: str, value: str) -> dict:
    """
    根据法律文书某个字段是某个值来查询具体的案号。
    可以输入的字段有['判决结果','原告','原告律师','审理法条依据',
    '文书类型','文件名','标题','案由','涉案金额',
    '胜诉方','被告','被告律师',]

    例如：
        输入：
        {"key": "原告",
         "value": "光明乳业股份有限公司"}
        输出：
        [{'案号': '(2020)苏06民初861号'},
         {'案号': '(2021)沪0104民初6181号'},
         {'案号': '(2021)沪0104民初17782号'},
         {'案号': '(2019)湘0111民初3091号'}]
    """
    url = f"https://{DOMAIN}/law_api/search_case_num_by_legal_document"

    data = {
        "key": key,
        "value": value
    }

    rsp = requests.post(url, json=data, headers=headers)
    print("search_case_num_by_legal_document", data, rsp.json())
    return rsp.json()


def search_company_and_registered_capital_by_industry(industry_name: str):
    """根据行业查询属于该行业的公司及其注册资本。"""
    company_names = search_company_name_by_info(key="所属行业", value=industry_name)
    if len(company_names) == 0:
        return []
    company_names = [company_name["公司名称"] for company_name in company_names]
    company_and_registered_capital_list = []
    for company_name in company_names:
        register_info = get_company_register(company_name)
        cnr_info = {
            "公司名称": company_name,
            "注册资本": register_info["注册资本"] if "注册资本" in register_info else None,
        }
        company_and_registered_capital_list.append(cnr_info)
    return company_and_registered_capital_list
