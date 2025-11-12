# coding:utf8
from utils.sqlite_db import inspect_db_structure, process_field, execute_sql
from agent.plan_agent import plan_agent
from agent.action_agent import action_agent
from prompt.prompts import comprehend_db_table_prompt, system_prompt, final_answer_prompt, self_reflection_prompt
from llm.llm_chain import base_llm_chain
import traceback


def agent_execute(question, llm, db_table_memory, print):
    message = [
        {"role": "system", "content": system_prompt},
    ]
    message.extend(db_table_memory)
    init_message = message
    cnt = 0
    while cnt < 2:
        print(f'当前问题轮数：{cnt + 1}')
        try:
            # 规划问题
            plan = plan_agent(question, message, llm, print)
            if plan == '此问题规划失败':
                print(f'轮数 {cnt + 1} 此问题规划失败')
                message = init_message
                cnt += 1
                continue
            message.extend(plan)

            # 执行问题
            action = action_agent(plan[-1]['content'], llm, db_table_memory, print)
            if action == '调用工具失败':
                print(f'轮数 {cnt + 1} 此问题调用工具失败')
                message = init_message
                cnt += 1
                continue

            # 最后的步骤为 answer
            answer = final_answer(question, llm, action, print)

            return answer
        except Exception as e:
            print(traceback.print_exc())
            print(f'当前问题重试中...error:{e}')
            message = init_message
            cnt += 1

    return '问题回答失败，重试次数达到上限'


def comprehend_db_table(llm, print):
    """llm 理解表结构"""
    print(f'llm 理解表结构')
    db_structure = inspect_db_structure()
    return [
        {"role": "user", "content": comprehend_db_table_prompt.format(db_structure=db_structure)},
    ]


def final_answer(question, llm, action, print):
    """从最后的步骤拿出最终 sql，去执行"""
    print(f'解析最后的答案！')
    sql = action[-1]['content']['sql']
    sql = process_field(sql)
    try:
        sql_res = execute_sql(sql, print)
    except Exception as e:
        sql_res = '执行失败'
        print(f'最后答案执行失败：{e}')
    answer = base_llm_chain(llm, final_answer_prompt, print, sql_res=sql_res, question=question)
    print(f'最后的答案成功返回：\n{answer}')
    return answer
