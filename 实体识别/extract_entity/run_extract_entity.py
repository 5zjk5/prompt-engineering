# coding:utf8
import json
import time
import traceback
import re
from extract_entity import extract_entity, key_map


def parse_entity(entity):
    """解析提取报错的"""
    entity = str(entity)
    re_entity = re.findall('but got (.*)', entity)
    if re_entity:
        re_entity = key_map(eval(re_entity[0]))
        return re_entity
    else:
        return entity


if __name__ == '__main__':
    start_time = time.time()
    with open('../data/question/初赛 B 榜question.json', encoding='utf8') as f:
        queries = f.readlines()

    for index, query in enumerate(queries):
        cur_start_time = time.time()
        print(f'-------------------{index} / {len(queries)}------------------------')
        query = json.loads(query)
        id = query['id']
        question = query['question']
        print(f'当前问题：{question}')

        # 提取实体
        try:
            entity = extract_entity(question=question)
            print(f'提取实体：{entity}')
        except Exception as e:
            print(f'提取实体失败！{e}')
            entity = parse_entity(e)
            print(f'解析后：{entity}')
        res = entity

        # 保存数据
        with open('../data/entity.json', "a+", encoding='utf-8') as json_file:
            json_file.write(json.dumps({'id': id, 'question': question, 'entity': res}, ensure_ascii=False) + '\n')

        cur_end_time = time.time()
        print(f'当前耗时：{cur_end_time - cur_start_time}s')

    end_time = time.time()
    print(f'总耗时：{end_time - start_time}s')
