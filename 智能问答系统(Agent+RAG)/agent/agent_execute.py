# coding:utf8
from utils.sqlite_db import generate_sql_by_question
from agent.agent import create_initialize_agent
from tools.sql_tools import sql_tools
import traceback


def agent_execute(question, llm, debug, agent_type='initialize_agent'):
    # 生成 sql
    generate_sql = generate_sql_by_question(question, llm)
    print(f'生成的 sql 语句为：{generate_sql}')
    if not generate_sql:
        return '生成 sql 失败！！！'

    # agent 执行 sql
    agent = create_initialize_agent(llm, sql_tools, debug)
    try:
        answer = agent.invoke({"input": f'最后用中文回答，问题：{question}，对应sql：' + generate_sql})
        answer = answer['output']
    except Exception as e:
        if debug:
            traceback.print_exc()
        answer = f'sql 执行出错-{e}'

    return answer
