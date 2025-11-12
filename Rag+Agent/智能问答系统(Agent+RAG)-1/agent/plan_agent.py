from prompt.prompts import plan_prompt, re_plan_prompt
from llm.llm_chain import base_llm_chain
from tools.sql_tools import sql_tools
import traceback


def plan_agent(question, message, llm, print):
    """根据问题，进行规划执行步骤"""
    cnt = 0
    error_reason = ''
    plan = ''
    while cnt < 2:
        try:
            print("开始执行规划步骤")
            plan = base_llm_chain(llm, plan_prompt, print,
                                  message=message, question=question, tools=sql_tools, error_reason=error_reason)
            plan = plan.strip('`json')
            plan = eval(plan)
            print(f'{plan}')
            return [
                {"role": "user", "content": plan_prompt.format(
                    message=None, question=question, tools=sql_tools, error_reason=error_reason)},
                {"role": "system", "content": plan}
            ]
        except Exception as e:
            print(traceback.print_exc())
            print(f"执行规划步骤失败，重新规划 error:{e}")
            error_reason = base_llm_chain(llm, re_plan_prompt, print, plan=plan, error=e)
            cnt += 1

    return '此问题规划失败'
