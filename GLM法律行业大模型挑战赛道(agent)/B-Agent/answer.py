# coding:utf8
import json
import time
import traceback
from agents.chat_router import route
from utils import parse_answer


debug = True


def answer(question: str):
    try:
        agent = route(question, agent_type='opanai_tool', debug=debug)
        messages = agent.invoke({"messages": [("human", question)]})
    except Exception as e:
        print(f'报错：{e} 再来一次')
        agent = route(question, agent_type='opanai_tool', debug=debug)
        messages = agent.invoke({"messages": [("human", question)]})
    return messages


def opanai_tool_agent(question, debug=debug):
    print('尝试 opanai_tool Agent！')
    agent = route(question, agent_type='opanai_tool', debug=debug)
    messages = agent.invoke({"messages": [("human", question)]})
    return messages


if __name__ == '__main__':
    start_time = time.time()
    with open('data/question/初赛 B 榜question.json', encoding='utf8') as f:
        queries = f.readlines()

    with open('data/answer/木下瞳_result.json', "w+", encoding='utf-8') as json_file:
        pass

    for index, query in enumerate(queries):
        cur_start_time = time.time()
        print(f'-------------------{index} / {len(queries)}------------------------')
        query = json.loads(query)
        id = query['id']
        question = query['question']
        print(f'当前问题：{question}')

        # 回答
        try:
            res = answer(question)
            res = parse_answer(res)
        except Exception as e:
            # traceback.print_exc()
            res = str(e)
        print(res)

        # 保存数据
        with open('data/answer/木下瞳_result.json', "a", encoding='utf-8') as json_file:
            json_file.write(json.dumps({'id': id, 'question': question, 'answer': res}, ensure_ascii=False) + '\n')

        cur_end_time = time.time()
        print(f'当前耗时：{cur_end_time - cur_start_time}s')

    end_time = time.time()
    print(f'总耗时：{end_time - start_time}s')
