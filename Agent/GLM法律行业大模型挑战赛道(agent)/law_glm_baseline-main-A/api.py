"""
@Time : 2024/6/12 15:16 
@Author : sunshb10145 
@File : api.py
@desc:
"""
import requests

domain = "comm.chatglm.cn"

# url = f"https://{domain}/law_api/get_legal_person"
url = f"https://{domain}/law_api/get_sub_company_info"
# url = f"https://{domain}/law_api/search_case_num_by_legal_document"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer 5876A40D2FA07E3D4EF9E0B1E4CF99D4EAB2D2F190DB1352'
}

data = {
    # "company_name": "广东天昊药业有限公司",
    "key": "关联上市公司全称",
    "value": "福安药业(集团)股份有限公司"
}

rsp = requests.post(url, json=data, headers=headers)
print(rsp.json())
