from llm.llm_chain import base_llm_chain
from prompt.prompts import action_start_prompt, step_action_prompt, re_action_prompt
from utils.sqlite_db import execute_sql, process_field
import traceback


def action_agent(plan, llm, message, print):
    """根据计划执行的 agent"""
    print("开始执行步骤")
    message.append({"role": "user", "content": action_start_prompt})
    for i, step in enumerate(plan):
        print(step)
        step_action = step[f'step{i + 1}']
        step_tool = step['tool']

        # 推理步骤
        infer_step_res = infer_step_action(llm, message, step_action, step_tool, print)
        if infer_step_res == '调用工具失败':
            return '调用工具失败'
        message.extend(infer_step_res)

    return message


def infer_step_action(llm, message, step_action, step_tool, print):
    """推理当前步骤，如果需要使用工具的调用工具"""
    cnt = 0
    error_reason = ''
    infer_step_res = ''
    while cnt < 2:
        try:
            infer_step_res = base_llm_chain(llm, step_action_prompt, print,
                                            message=message, step_action=step_action, error_reason=error_reason)

            # 解析 json
            try:
                infer_step_res = eval(''.join(infer_step_res.split('```')[:-1]).strip('`json'))
            except:
                infer_step_res = eval(infer_step_res.strip('`json'))
            print(infer_step_res)

            if step_tool or infer_step_res['sql']:
                print('调用执行 sql 工具')
                sql = infer_step_res['sql']
                sql = process_field(sql)
                sql_res = execute_sql(sql, print)
                if sql_res is None:  # 超时重新生成
                    # cnt += 1
                    # message.append(
                    #     [
                    #         {"role": "user", "content": f'sql 执行超时了，请重新优化 SQL：{sql}'},
                    #         {"role": "assistant", "content": '好的，接下来的我将根据问题进行 SQL 优化。'}
                    #     ]
                    # )
                    # continue
                    return [
                                {"role": "user", "content": f'sql 执行超时了，后面的步骤需要生成 SQL，需要注意执行效率及性能问题。'},
                                {"role": "assistant", "content": '好的，接下来的我将根据问题进行 SQL 优化。'}
                            ]
                print('sql 执行成功')

            return [
                {"role": "user", "content": step_action_prompt.format(message=None, step_action=step_action,
                                                                      error_reason=error_reason)},
                {"role": "assistant", "content": infer_step_res}
            ]
        except Exception as e:
            print(traceback.print_exc())
            print(f'当前步骤失败，重新执行！error:{e}')
            error_reason = base_llm_chain(llm, re_action_prompt, print, infer_step_res=infer_step_res, error=e)
            cnt += 1

    return '调用工具失败'
