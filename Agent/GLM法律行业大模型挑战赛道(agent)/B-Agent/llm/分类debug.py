import json
import time
from router_chain import router_chain

with open('../data/question/初赛 B 榜question.json', encoding='utf8') as f:
    queries = f.readlines()

for index, query in enumerate(queries):
    cur_start_time = time.time()
    print(f'-------------------{index} / {len(queries)}------------------------')
    query = json.loads(query)
    id = query['id']
    question = query['question']
    if question != '爱玛科技集团股份有限公司涉案金额最高的法院的负责人是？':
        continue
    print(f'当前问题：{question}')
    res = router_chain.invoke({
        "question": question
    })
    print(res)
