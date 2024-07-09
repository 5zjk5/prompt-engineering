# coding:utf8
from typing import List, Union, Dict, Any
import requests


DOMAIN = "comm.chatglm.cn"
TEAM_TOKEN = "CFBC7E73FDE49C45B4289ED85720C43FCC5402D28158E0EB"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {TEAM_TOKEN}'
}


def get_company_info(key, value) -> str:
    """
    根据上市公司名称、简称或代码查找上市公司信息

    need_fields 传入空列表，则表示返回所有字段，否则返回填入的字段

    输入：
        {"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []}
        {"query_conds": {"公司简称": "妙可蓝多"}, "need_fields": []}
        {"query_conds": {"公司代码": "600882"}, "need_fields": []}
    输出：
        {
     "公司名称": "上海妙可蓝多食品科技股份有限公司",
     "公司简称": "妙可蓝多",
     "英文名称": "Shanghai Milkground Food Tech Co., Ltd.",
     "关联证券": "",
     "公司代码": "600882",
     "曾用简称": "大成股份>> *ST大成>> 华联矿业>> 广泽股份",
     "所属市场": "上交所",
     "所属行业": "食品制造业",
     "成立日期": "1988-11-29",
     "上市日期": "1995-12-06",
     "法人代表": "柴琇",
     "总经理": "柴琇",
     "董秘": "谢毅",
     "邮政编码": "200136",
     "注册地址": "上海市奉贤区工业路899号8幢",
     "办公地址": "上海市浦东新区金桥路1398号金台大厦10楼",
     "联系电话": "021-50188700",
     "传真": "021-50188918",
     "官方网址": "www.milkground.cn",
     "电子邮箱": "ir@milkland.com.cn",
     "入选指数": "国证Ａ指,巨潮小盘",
     "主营业务": "以奶酪、液态奶为核心的特色乳制品的研发、生产和销售，同时公司也从事以奶粉、黄油为主的乳制品贸易业务。",
     "经营范围": "许可项目：食品经营；食品互联网销售；互联网直播服务（不含新闻信息服务、网络表演、网络视听节目）；互联网信息服务；进出口代理。（依法须经批准的项目，经相关部门批准后方可开展经营活动，具体经营项目以相关部门批准文件或许可证件为准）。一般项目：乳制品生产技术领域内的技术开发、技术咨询、技术服务、技术转让；互联网销售（除销售需要许可的商品）；互联网数据服务；信息系统集成服务；软件开发；玩具销售。（除依法须经批准的项目外，凭营业执照依法自主开展经营活动）",
     "机构简介": "公司是1988年11月10日经山东省体改委鲁体改生字(1988)第56号文批准，由山东农药厂发起，采取社会募集方式组建的以公有股份为主体的股份制企业。1988年12月15日,经中国人民银行淄博市分行以淄银字(1988)230号文批准，公开发行股票。 1988年12月经淄博市工商行政管理局批准正式成立山东农药工业股份有限公司(营业执照:16410234)。",
     "每股面值": "1.0",
     "首发价格": "1.0",
     "首发募资净额": "4950.0",
     "首发主承销商": ""
        }
    """
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_company_register(key, value) -> str:
    """
    根据公司名称，查询工商信息

    输入：
        {"query_conds": {"公司名称": "天能电池集团股份有限公司"}, "need_fields": []}
    输出：
        {
     "公司名称": "天能电池集团股份有限公司",
     "登记状态": "存续",
     "统一社会信用代码": "913305007490121183",
     "法定代表人": "杨建芬",
     "注册资本": "97210",
     "成立日期": "2003-03-13",
     "企业地址": "浙江省长兴县煤山镇工业园区",
     "联系电话": "0572-6029388",
     "联系邮箱": "dshbgs@tiannenggroup.com",
     "注册号": "330500400001780",
     "组织机构代码": "74901211-8",
     "参保人数": "709",
     "行业一级": "制造业",
     "行业二级": "电气机械和器材制造业",
     "行业三级": "电池制造",
     "曾用名": "天能电池集团有限公司,\n浙江天能电池有限公司",
     "企业简介": "天能集团成立于1986年，地处长三角腹地—— “中国绿色动力能源中心”浙江长兴，主要以电动车环保动力电池制造为主，集新能源镍氢、锂离子电池，风能、太阳能储能电池以及再生铅资源回收、循环利用等新能源的研发、生产、销售为一体，是目前国内首屈一指的绿色动力能源制造商。集团实力雄厚，管理科学，行业地位优势明显，于2007年6月11日，以中国动力电池第一股，在香港主板成功上市（00819.HK）。目前，集团已发展成为拥有25家国内全资子公司，3家境外公司，2013年销售收入达500亿，员工20000余名的大型国际化集团公司。集团拥有浙江长兴、江苏沭阳、安徽芜湖、安徽界首、河南濮阳五大生产基地，总资产近70亿元。公司主导产品电动车动力电池的产销量连续十五年位居全国同行业首位。集团是国家重点扶持技术企业、国家火炬计划重点技术企业，全国轻工行业先进集体、浙江省工业行业龙头骨干企业、国家蓄电池标准化委员会副主任委员单位。集团经营规模位居中国制造业企业500强、中国民营企业500强、中国电池行业十强、浙江省百强企业、浙江省民营企业100强。拥有国家级博士后工作站、院士专家工作站、省级企业技术中心、省级高新技术研究开发中心。近年来，先后开发国家级重点新产品10项，创新国家专利近600余项、省级新产品和高新技术产品100余项，同时承担国家火炬计划和星火计划项目10余项。集团“天能”牌电池先后被评为国家重点新产品、浙江省名牌产品、浙江省高新技术产品；“天能”商标先后荣获驰名商标、浙江省着名商标；天能品牌荣获2008中国动力电池最佳品牌、中国最具价值品牌500强、亚洲品牌500强，天能电池荣获2009年度最值得消费者信赖的电动车电池品牌，天能集团荣获中国电动车行业发展突出贡献奖。为响应国家大力发展循环经济的号召，天能集团将积极致力于新能源产业的发展，努力创新创业，实现“矢志成为全球领先的绿色能源供应商”的战略目标，争取为改善民生发展、践行产业报国、构建和谐社会作出更大的贡献。",
     "经营范围": "高性能电池的研发、生产、销售；锂离子电池、燃料电池及其他储能环保电池、新型电极材料的研究开发、生产、销售；货物进出口和技术进出口（国家限定公司经营或禁止进出口的商品和技术除外）。（依法须经批准的项目，经相关部门批准后方可开展经营活动）"
        }
    """
    if key != '公司名称':
        key = '公司名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_register"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_company_register_name(key, value) -> str:
    """
    根据统一社会信用代码查询公司名称

    输入：
        {"query_conds": {"统一社会信用代码": "913305007490121183"}, "need_fields": []}
    输出：
        {'公司名称': '天能电池集团股份有限公司'}
    """
    if key != '统一社会信用代码':
        key = '统一社会信用代码'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_register_name"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_sub_company_info(key, value) -> str:
    """
    根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息

    输入：
        {"query_conds": {"公司名称": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []}
    输出：
        {
     "关联上市公司全称": "上海航天汽车机电股份有限公司",
     "上市公司关系": "子公司",
     "上市公司参股比例": "87.5",
     "上市公司投资金额": "8.54亿",
     "公司名称": "上海爱斯达克汽车空调系统有限公司"
        }
    """
    if key != '公司名称':
        key = '公司名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_sub_company_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_sub_company_info_list(key, value) -> str:
    """
    根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list

    输入：
        {"query_conds": {"关联上市公司全称": "上海航天汽车机电股份有限公司"}, "need_fields": []}
    输出：
        [
            {
             "关联上市公司全称": "上海航天汽车机电股份有限公司",
             "上市公司关系": "子公司",
             "上市公司参股比例": "100.0",
             "上市公司投资金额": "8800.00万",
             "公司名称": "甘肃神舟光伏电力有限公司"
            }
            ......
        ]
    """
    if key != '关联上市公司全称':
        key = '关联上市公司全称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_sub_company_info_list"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_legal_document(key, value) -> str:
    """
    根据案号查询裁判文书相关信息

    输入：
        {"query_conds": {"案号": "(2019)沪0115民初61975号"}, "need_fields": []}
    输出：
        {
     "关联公司": "上海爱斯达克汽车空调系统有限公司",
     "标题": "上海爱斯达克汽车空调系统有限公司与上海逸测检测技术服务有限公司服务合同纠纷一审民事判决书",
     "案号": "(2019)沪0115民初61975号",
     "文书类型": "民事判决书",
     "原告": "上海爱斯达克汽车空调系统有限公司",
     "被告": "上海逸测检测技术服务有限公司",
     "原告律师事务所": "",
     "被告律师事务所": "上海世韬律师事务所",
     "案由": "服务合同纠纷",
     "涉案金额": "1254802.58",
     "判决结果": "一、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司测试费1,254,802.58元; \\n \\n二、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司违约金71,399.68元 。  \\n \\n负有金钱给付义务的当事人如未按本判决指定的期间履行给付金钱义务,应当依照《中华人民共和国民事诉讼法》第二百五十三条之规定,加倍支付迟延履行期间的债务利息 。  \\n \\n案件受理费16,736元,减半收取计8,368元,由被告上海逸测检测技术服务有限公司负担 。  \\n \\n如不服本判决,可在判决书送达之日起十五日内向本院递交上诉状,并按对方当事人的人数提出副本,上诉于上海市第一中级人民法院 。 ",
     "日期": "2019-12-09 00:00:00",
     "文件名": "（2019）沪0115民初61975号.txt"
        }
    """
    if key != '案号':
        key = '案号'
    value1 = value
    value2 = value
    if '(' in value1:
        value1 = value1.replace('(', '（').replace(')', '）')
    else:
        value2 = value2.replace('（', '(').replace('）', ')')

    query_conds = {"query_conds": {key: value1}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_document"
    rsp = requests.post(url, json=query_conds, headers=headers)
    if rsp.json():
        return str(rsp.json())
    else:
        query_conds = {"query_conds": {key: value2}, "need_fields": []}
        url = f"https://{DOMAIN}/law_api/s1_b/get_legal_document"
        rsp = requests.post(url, json=query_conds, headers=headers)
        return str(rsp.json())


def get_legal_document_list(key, value) -> str:
    """
    根据关联公司查询所有裁判文书相关信息list

    输入：
        {"query_conds": {"关联公司": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []}
    输出：
        [
            {
     "关联公司": "上海爱斯达克汽车空调系统有限公司",
     "标题": "上海爱斯达克汽车空调系统有限公司与上海逸测检测技术服务有限公司服务合同纠纷一审民事判决书",
     "案号": "(2019)沪0115民初61975号",
     "文书类型": "民事判决书",
     "原告": "上海爱斯达克汽车空调系统有限公司",
     "被告": "上海逸测检测技术服务有限公司",
     "原告律师事务所": "",
     "被告律师事务所": "上海世韬律师事务所",
     "案由": "服务合同纠纷",
     "涉案金额": "1254802.58",
     "判决结果": "一、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司测试费1,254,802.58元; \\n \\n二、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司违约金71,399.68元 。  \\n \\n负有金钱给付义务的当事人如未按本判决指定的期间履行给付金钱义务,应当依照《中华人民共和国民事诉讼法》第二百五十三条之规定,加倍支付迟延履行期间的债务利息 。  \\n \\n案件受理费16,736元,减半收取计8,368元,由被告上海逸测检测技术服务有限公司负担 。  \\n \\n如不服本判决,可在判决书送达之日起十五日内向本院递交上诉状,并按对方当事人的人数提出副本,上诉于上海市第一中级人民法院 。 ",
     "日期": "2019-12-09 00:00:00",
     "文件名": "（2019）沪0115民初61975号.txt"
            }
            .......
        ]
    """
    if key != '关联公司':
        key = '关联公司'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_document_list"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_court_info(key, value) -> str:
    """
    根据法院名称查询法院名录相关信息

    输入：
        {"query_conds": {"法院名称": "上海市浦东新区人民法院"}, "need_fields": []}
    输出：
        {
     "法院名称": "上海市浦东新区人民法院",
     "法院负责人": "朱丹",
     "成立日期": "2019-05-16",
     "法院地址": "上海市浦东新区丁香路611号",
     "法院联系电话": "-",
     "法院官网": "-"
        }
    """
    if key != '法院名称':
        key = '法院名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_court_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_court_code(key, value) -> str:
    """
    根据法院名称或者法院代字查询法院代字等相关数据

    输入：
        {"query_conds": {"法院名称": "上海市浦东新区人民法院"}, "need_fields": []}
        {"query_conds": {"法院代字": "沪0115"}, "need_fields": []}
    输出：
        {
     "法院名称": "上海市浦东新区人民法院",
     "行政级别": "市级",
     "法院级别": "基层法院",
     "法院代字": "沪0115",
     "区划代码": "310115",
     "级别": "1"
        }
    """
    if key == '案号':
        return "应该使用跟案号相关的工具，如：'get_legal_document'或'get_legal_abstract'或'get_xzgxf_info'"
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_court_code"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_lawfirm_info(key, value) -> str:
    """
    根据律师事务所查询律师事务所名录

    输入：
        {"query_conds": {"律师事务所名称": "爱德律师事务所"}, "need_fields": []}
    输出：
        {
     "律师事务所名称": "爱德律师事务所",
     "律师事务所唯一编码": "31150000E370803331",
     "律师事务所负责人": "巴布",
     "事务所注册资本": "10万元人民币",
     "事务所成立日期": "1995-03-14",
     "律师事务所地址": "呼和浩特市赛罕区大学西街110号丰业大厦11楼",
     "通讯电话": "0471-3396155",
     "通讯邮箱": "kehufuwubu@ardlaw.cn",
     "律所登记机关": "内蒙古自治区呼和浩特市司法局"
        }
    """
    if key != '律师事务所名称':
        key = '律师事务所名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_lawfirm_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_lawfirm_log(key, value) -> str:
    """
    根据律师事务所查询律师事务所统计数据

    输入：
        {"query_conds": {"律师事务所名称": "北京市金杜律师事务所"}, "need_fields": []}
    输出：
        {
     "律师事务所名称": "北京市金杜律师事务所",
     "业务量排名": "2",
     "服务已上市公司": "68",
     "报告期间所服务上市公司违规事件": "23",
     "报告期所服务上市公司接受立案调查": "3"
        }
    """
    if key != '律师事务所名称':
        key = '律师事务所名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_lawfirm_log"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_address_info(key, value) -> str:
    """
    根据地址查该地址对应的省份城市区县

    输入：
        {"query_conds": {"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}, "need_fields": []}
    输出：
        {
     "地址": "西藏自治区那曲地区安多县帕那镇中路13号",
     "省份": "西藏自治区",
     "城市": "那曲市",
     "区县": "安多县"
        }
    """
    if key != '地址':
        key = '地址'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_address_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_address_code(query_conds: Dict[str, Union[dict, List[str]]]) -> dict:
    """
    根据省市区查询区划代码

    输入：
        {"query_conds": {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}, "need_fields": []}
    输出：
        {
     "省份": "西藏自治区",
     "城市": "拉萨市",
     "城市区划代码": "540100000000",
     "区县": "城关区",
     "区县区划代码": "540102000000"
        }
    """
    if not query_conds['省份'] or not query_conds['城市'] or not query_conds['区县']:
        return '需要先查询地址的省份，城市，区县'
    query_conds = {"query_conds": query_conds, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_address_code"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return rsp.json()


def get_temp_info(query_conds: Dict[str, Union[dict, List[str]]]) -> dict:
    """
    根据日期及省份城市查询天气相关信息

    输入：
        {"query_conds": {"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}, "need_fields": []}
    输出：
        {
     "日期": "2020年1月1日",
     "省份": "北京市",
     "城市": "北京市",
     "天气": "晴",
     "最高温度": "11",
     "最低温度": "1",
     "湿度": "55"
        }
    """
    if not query_conds['省份'] or not query_conds['城市'] or '市' not in query_conds['城市']:
        return '需要先查询地址的省份，城市'
    query_conds = {"query_conds": query_conds, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_temp_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return rsp.json()


def get_legal_abstract(key, value) -> str:
    """
    根据案号查询文本摘要

    输入：
        {"query_conds": {"案号": "（2019）沪0115民初61975号"}, "need_fields": []}
    输出：
        {
     "文件名": "（2019）沪0115民初61975号.txt",
     "案号": "（2019）沪0115民初61975号",
     "文本摘要": "原告上海爱斯达克汽车空调系统有限公司与被告上海逸测检测技术服务有限公司因服务合同纠纷一案，原告请求被告支付检测费1,254,802.58元、延迟履行违约金71,399.68元及诉讼费用。被告辩称，系争合同已终止，欠款金额应为499,908元，且不认可违约金。\n法院认为，原告与腾双公司签订的测试合同适用于原被告，原告提供的测试服务应得到被告支付。依照《中华人民共和国合同法》第六十条、第一百零九条,《中华人民共和国民事诉讼法》第六十四条第一款,《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第九十条之规定判决被告支付原告检测费1,254,802.58元及违约金71,399.68元。"
        }
    """
    if key != '案号':
        key = '案号'
    value1 = value
    value2 = value
    if '(' in value1:
        value1 = value1.replace('(', '（').replace(')', '）')
    else:
        value2 = value2.replace('（', '(').replace('）', ')')

    query_conds = {"query_conds": {key: value1}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_abstract"
    rsp = requests.post(url, json=query_conds, headers=headers)
    if rsp.json():
        return str(rsp.json())
    else:
        query_conds = {"query_conds": {key: value2}, "need_fields": []}
        url = f"https://{DOMAIN}/law_api/s1_b/get_legal_abstract"
        rsp = requests.post(url, json=query_conds, headers=headers)
        return str(rsp.json())


def get_xzgxf_info(key, value) -> str:
    """
    根据案号查询限制高消费相关信息

    输入：
        { "query_conds": {"案号": "（2018）鲁0403执1281号"}, "need_fields": [] }
    输出：
        {
     "限制高消费企业名称": "枣庄西能新远大天然气利用有限公司",
     "案号": "（2018）鲁0403执1281号",
     "法定代表人": "高士其",
     "申请人": "枣庄市人力资源和社会保障局",
     "涉案金额": "12000",
     "执行法院": "山东省枣庄市薛城区人民法院",
     "立案日期": "2018-11-16 00:00:00",
     "限高发布日期": "2019-02-13 00:00:00"
        }
    """
    if key != '案号':
        key = '案号'
    value1 = value
    value2 = value
    if '(' in value1:
        value1 = value1.replace('(', '（').replace(')', '）')
    else:
        value2 = value2.replace('（', '(').replace('）', ')')

    query_conds = {"query_conds": {key: value1}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info"
    rsp = requests.post(url, json=query_conds, headers=headers)
    if rsp.json():
        return str(rsp.json())
    else:
        query_conds = {"query_conds": {key: value2}, "need_fields": []}
        url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info"
        rsp = requests.post(url, json=query_conds, headers=headers)
        return str(rsp.json())

def get_xzgxf_info_list(key, value) -> str:
    """
    根据企业名称查询所有限制高消费相关信息list

    输入：
        {"query_conds": {"限制高消费企业名称": "欣水源生态环境科技有限公司"}, "need_fields": []}
    输出：
        {
     "限制高消费企业名称": "欣水源生态环境科技有限公司",
     "案号": "（2023）黔2731执恢130号",
     "法定代表人": "刘福云",
     "申请人": "四川省裕锦建设工程有限公司惠水分公司",
     "涉案金额": "7500000",
     "执行法院": "贵州省黔南布依族苗族自治州惠水县人民法院",
     "立案日期": "2023-08-04 00:00:00",
     "限高发布日期": "2023-11-09 00:00:00"
        }
    """
    if key != '限制高消费企业名称':
        key = '限制高消费企业名称'
    query_conds = {"query_conds": {key: value}, "need_fields": []}
    url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info_list"
    rsp = requests.post(url, json=query_conds, headers=headers)
    return str(rsp.json())


def get_sum(nums: List[Union[int, float, str]]) -> float:
    """
    求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿，如"1万"【具体实现详见附录】

    输入：
        [1, 2, 3, 4, 5]
    输出：
        15
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_sum"
    rsp = requests.post(url, json=nums, headers=headers)
    return rsp.json()


def rank(sort_dict: Dict[str, List[Union[str, float]]]) -> List[Any]:
    """
    排序接口，返回按照values排序的keys【具体实现详见附录】

    输入：
        { "keys": ["a", "b", "c"], "values": [2, 1, 3] }
    输出：
        ['b', 'a', 'c']
    """
    url = f"https://{DOMAIN}/law_api/s1_b/rank"
    rsp = requests.post(url, json=sort_dict, headers=headers)
    return rsp.json()


def save_dict_list_to_word(data) -> None:
    """
    通过传入结构化信息，制作生成公司数据报告（demo）

    输入：
        {'company_name': '北京碧水源科技股份有限公司', 'dict_list': "{'工商信息': [{'公司名称': '北京碧水源科技股份有限公司', '登记状态': '存续', '统一社会信用代码': '91110000802115985Y', '参保人数': '351', '行业一级': '科学研究和技术服务业', '行业二级': '科技推广和应用服务业', '行业三级': '其他科技推广服务业'}], '子公司信息 ': [{'关联上市公司全称': '北京碧水源科技股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': 100.0, '上市公司投资金额': '1.06亿', '公司名称': '北京碧海 环境科技有限公司'}], '裁判文书': [{'关联公司': '北京碧水源科技股份有限公司', '原告': '四川帝宇水利水电工程有限公司', '被告': '成都碧水源江环保科技有限公司,北京 碧水源科技股份有限公司', '案由': '建设工程施工合同纠纷', '涉案金额': 0.0, '日期': Timestamp('2019-07-23 00:00:00')}], '限制高消费': [{'限制高消费企业名称': '南 京仙林碧水源污水处理有限公司', '案号': '（2024）苏0113执1601号', '申请人': '苏华建设集团有限公司', '涉案金额': '-', '立案日期': Timestamp('2024-04-07 00:00:00'), '限高发布日期': Timestamp('2024-06-24 00:00:00')}]}"}
    输出：
        输出到 /data/save_dict_list_to_word 目录
    """
    url = f"https://{DOMAIN}/law_api/s1_b/save_dict_list_to_word"
    rsp = requests.post(url, json=data, headers=headers)
    open(f"../data/save_dict_list_to_word/{data['company_name']}.docx", "wb").write(rsp.content)


def get_citizens_sue_citizens(data) -> str:
    """
    民事起诉状(公民起诉公民)

    输入：
        { '原告': '张三', '原告性别': '男', '原告生日': '1976-10-2', '原告民族': '汉', '原告工作单位': 'XXX', '原告地址': '中国', '原告联系方式': '123456', '原告委托诉讼代理人': '李四', '原告委托诉讼代理人联系方式': '421313', '被告': '王五', '被告性别': '女', '被告生日': '1975-02-12', '被告民族': '汉', '被告工作单位': 'YYY', '被告地址': '江苏', '被告联系方式': '56354321', '被告委托诉讼代理人': '赵六', '被告委托诉讼代理人联系方式': '09765213', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' }
    输出：
        民事起诉状（公民起诉公民）
        原告：张三，性别：男，出生日期：1976-10-2，民族：汉，工作单位：XXX，地址：中国，联系方式：123456。
        原告委托诉讼代理人：李四，联系方式：421313。
        被告：王五，性别：女，出生日期：1975-02-12，民族：汉，工作单位：YYY，地址：江苏，联系方式：56354321。
        被告委托诉讼代理人：赵六，联系方式：09765213。
        .......
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_citizens_sue_citizens"
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()


def get_company_sue_citizens(data) -> str:
    """
    民事起诉状(公司起诉公民)

    输入：
        { '原告': '上海公司', '原告地址': '上海', '原告法定代表人': '张三', '原告联系方式': '872638', '原告委托诉讼代理人': 'B律师事务所', '原告委托诉讼代理人联系方式': '5678900', '被告': '王五', '被告性别': '女', '被告生日': '1975-02-12', '被告民族': '汉', '被告工作单位': 'YYY', '被告地址': '江苏', '被告联系方式': '56354321', '被告委托诉讼代理人': '赵六', '被告委托诉讼代理人联系方式': '09765213', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' }
    输出：
        民事起诉状（公司起诉公民）
        原告：上海公司，地址：上海。法定代表人（负责人）：张三，联系方式：872638。
        原告委托诉讼代理人：B律师事务所，联系方式：5678900。
        被告：王五，性别：女，出生日期：1975-02-12，民族：汉，
        ......
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_sue_citizens"
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()


def get_citizens_sue_company(data) -> str:
    """
    民事起诉状(公民起诉公司)

    输入：
        { '原告': '张三', '原告性别': '男', '原告生日': '1976-10-2', '原告民族': '汉', '原告工作单位': 'XXX', '原告地址': '中国', '原告联系方式': '123456', '原告委托诉讼代理人': '李四', '原告委托诉讼代理人联系方式': '421313', '被告': '王五公司', '被告地址': '公司地址', '被告法定代表人': '赵四', '被告联系方式': '98766543', '被告委托诉讼代理人': 'C律师事务所', '被告委托诉讼代理人联系方式': '425673398', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' }
    输出：
        民事起诉状（公民起诉公司）
        原告：张三，性别：男，出生日期：1976-10-2，民族：汉，工作单位：XXX，地址：中国，联系方式：123456。
        原告委托诉讼代理人：李四，联系方式：421313。
        被告：王五公司，地址：公司地址。法定代表人（负责人）：赵四，联系方式：98766543。
        被告委托诉讼代理人：C律师事务所，联系方式：425673398。
        ......
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_citizens_sue_company"
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()


def get_company_sue_company(data) -> str:
    """
    民事起诉状(公司起诉公司)

    输入：
        { '原告': '上海公司', '原告地址': '上海', '原告法定代表人': '张三', '原告联系方式': '872638', '原告委托诉讼代理人': 'B律师事务所', '原告委托诉讼代理人联系方式': '5678900', '被告': '王五公司', '被告地址': '公司地址', '被告法定代表人': '赵四', '被告联系方式': '98766543', '被告委托诉讼代理人': 'C律师事务所', '被告委托诉讼代理人联系方式': '425673398', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' }
    输出：
        民事起诉状（公司起诉公司）
        原告：上海公司，地址：上海。法定代表人（负责人）：张三，联系方式：872638。
        原告委托诉讼代理人：B律师事务所，联系方式：5678900。
        被告：王五公司，地址：公司地址。法定代表人（负责人）：赵四，联系方式：98766543。
        ......
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_sue_company"
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()


if __name__ == '__main__':
    # res = get_company_info({"query_conds": {"公司代码": "600882"}, "need_fields": []})
    # res = get_company_register({"query_conds": {"公司名称": "天能电池集团股份有限公司"}, "need_fields": []})
    # res = get_company_register_name({"query_conds": {"统一社会信用代码": "913305007490121183"}, "need_fields": []})
    # res = get_sub_company_info({"query_conds": {"公司名称": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []})
    # res = get_sub_company_info_list({"关联上市公司全称": "上海航天汽车机电股份有限公司"})
    res = get_legal_document({"query_conds": {"案号": "(2019)沪0115民初61975号"}, "need_fields": []})
    # res = get_legal_document_list({"query_conds": {"关联公司": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []})
    # res = get_court_info({"query_conds": {"法院名称": "上海市浦东新区人民法院"}, "need_fields": []})
    # res = get_court_code({"query_conds": {"法院代字": "沪0115"}, "need_fields": []})
    # res = get_lawfirm_info({"query_conds": {"律师事务所名称": "爱德律师事务所"}, "need_fields": []})
    # res = get_lawfirm_log({"query_conds": {"律师事务所名称": "北京市金杜律师事务所"}, "need_fields": []})
    # res = get_address_info({"query_conds": {"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}, "need_fields": []})
    # res = get_address_code({"query_conds": {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}, "need_fields": []})
    # res = get_temp_info({"query_conds": {"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}, "need_fields": []})
    # res = get_legal_abstract({"query_conds": {"案号": "（2019）沪0115民初61975号"}, "need_fields": []})
    # res = get_xzgxf_info({ "query_conds": {"案号": "（2018）鲁0403执1281号"}, "need_fields": [] })
    # res = get_xzgf_info_list({"query_conds": {"限制高消费企业名称": "欣水源生态环境科技有限公司"}, "need_fields": []})
    # res = get_sum([1, 2, 3, 4, 5])
    # res = rank({"keys": ["a", "b", "c"], "values": [2, 1, 3]})
    # res = save_dict_list_to_word({'company_name': '北京碧水源科技股份有限公司', 'dict_list': "{'工商信息': [{'公司名称': '北京碧水源科技股份有限公司', '登记状态': '存续', '统一社会信用代码': '91110000802115985Y', '参保人数': '351', '行业一级': '科学研究和技术服务业', '行业二级': '科技推广和应用服务业', '行业三级': '其他科技推广服务业'}], '子公司信息 ': [{'关联上市公司全称': '北京碧水源科技股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': 100.0, '上市公司投资金额': '1.06亿', '公司名称': '北京碧海 环境科技有限公司'}], '裁判文书': [{'关联公司': '北京碧水源科技股份有限公司', '原告': '四川帝宇水利水电工程有限公司', '被告': '成都碧水源江环保科技有限公司,北京 碧水源科技股份有限公司', '案由': '建设工程施工合同纠纷', '涉案金额': 0.0, '日期': Timestamp('2019-07-23 00:00:00')}], '限制高消费': [{'限制高消费企业名称': '南 京仙林碧水源污水处理有限公司', '案号': '（2024）苏0113执1601号', '申请人': '苏华建设集团有限公司', '涉案金额': '-', '立案日期': Timestamp('2024-04-07 00:00:00'), '限高发布日期': Timestamp('2024-06-24 00:00:00')}]}"})
    # res = get_citizens_sue_citizens({ '原告': '张三', '原告性别': '男', '原告生日': '1976-10-2', '原告民族': '汉', '原告工作单位': 'XXX', '原告地址': '中国', '原告联系方式': '123456', '原告委托诉讼代理人': '李四', '原告委托诉讼代理人联系方式': '421313', '被告': '王五', '被告性别': '女', '被告生日': '1975-02-12', '被告民族': '汉', '被告工作单位': 'YYY', '被告地址': '江苏', '被告联系方式': '56354321', '被告委托诉讼代理人': '赵六', '被告委托诉讼代理人联系方式': '09765213', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' })
    # res = get_company_sue_citizens({ '原告': '上海公司', '原告地址': '上海', '原告法定代表人': '张三', '原告联系方式': '872638', '原告委托诉讼代理人': 'B律师事务所', '原告委托诉讼代理人联系方式': '5678900', '被告': '王五', '被告性别': '女', '被告生日': '1975-02-12', '被告民族': '汉', '被告工作单位': 'YYY', '被告地址': '江苏', '被告联系方式': '56354321', '被告委托诉讼代理人': '赵六', '被告委托诉讼代理人联系方式': '09765213', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' })
    # res = get_citizens_sue_company({ '原告': '张三', '原告性别': '男', '原告生日': '1976-10-2', '原告民族': '汉', '原告工作单位': 'XXX', '原告地址': '中国', '原告联系方式': '123456', '原告委托诉讼代理人': '李四', '原告委托诉讼代理人联系方式': '421313', '被告': '王五公司', '被告地址': '公司地址', '被告法定代表人': '赵四', '被告联系方式': '98766543', '被告委托诉讼代理人': 'C律师事务所', '被告委托诉讼代理人联系方式': '425673398', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' })
    # res = get_company_sue_company({ '原告': '上海公司', '原告地址': '上海', '原告法定代表人': '张三', '原告联系方式': '872638', '原告委托诉讼代理人': 'B律师事务所', '原告委托诉讼代理人联系方式': '5678900', '被告': '王五公司', '被告地址': '公司地址', '被告法定代表人': '赵四', '被告联系方式': '98766543', '被告委托诉讼代理人': 'C律师事务所', '被告委托诉讼代理人联系方式': '425673398', '诉讼请求': 'AA纠纷', '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08' })
    print(res)
    pass