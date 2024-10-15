from llm.llm_glm import zhipu_glm_4
from llm.llm_chain import base_llm_chain
from utils.prompt import react_prompt, begin_react_prompt, query_rewrite_prompt, agent_scratchpad_prompt, final_answer_prompt
from tools.tools import tool_names, tools, tool_dict
import pprint
import traceback


def agent(query, llm, max_time=3):
    # query 改写，结合工具识别潜在意图
    query_rewrite = base_llm_chain(llm, query_rewrite_prompt, tools=tools, query=query)
    print(f'问题改写，识别潜在意图：\n{query_rewrite}')
    print('=====================================')

    # 初始解决问题的思考
    thought = base_llm_chain(llm, begin_react_prompt, tools=tools, query=query, query_rewrite=query_rewrite)
    print(f'解决此问题的思考 Thought：\n{thought}')
    print('=====================================')

    # 思考怎么做
    agent_scratchpad = None
    # 所有 action 结果保存
    all_action_res = []

    cnt = 0
    while cnt < max_time:
        try:
            # action 结果
            action_res = base_llm_chain(llm, react_prompt,
                                 tools=tools, tool_names=tool_names, query=query_rewrite, agent_scratchpad=agent_scratchpad)
            action_res = action_res.strip('`json').replace('{}', '')
            action_res = eval(action_res)

            # 判断是否需要调用工具，action 调用工具并更新结果到 Observation 行动的结果
            if action_res['Action']:
                action_tool_res = action_use_tool(action_res)
                action_res['Observation'] = action_tool_res
            all_action_res.append({action_res['Thought']: action_res['Observation']})
            pprint.pprint(action_res)
            print('=====================================')

            # 观察下一步需要做什么
            agent_scratchpad = next_action(query, thought, all_action_res, tools, llm)
            print(f'下一步需要做什么：\n{agent_scratchpad}')
            print('=====================================')

            # 判断是否是最后一个 action
            if 'no' in agent_scratchpad or 'No' in agent_scratchpad or 'NO' in agent_scratchpad:
                return final_answer(query, query_rewrite, all_action_res, llm)
        except Exception as err:
            print(traceback.format_exc())
            print(f'失败次数 {cnt + 1}/{max_time}, err: {err}')
            cnt += 1
            agent_scratchpad = thought
            all_action_res = []

    return '超过最大次数，回答失败'


def action_use_tool(action_res):
    if isinstance(action_res['Action'], str):
        action_res['Action'] = eval(action_res['Action'])
    tool = action_res['Action']['tool']
    tool_func = tool_dict[tool]
    if isinstance(action_res['Action Input'], str):
        action_res['Action Input'] = eval(action_res['Action Input'])
    tool_input = action_res['Action Input']
    tool_result = tool_func(**tool_input)  # ** 来解包字典作为关键字参数
    return tool_result


def next_action(query, thought, all_action_res, tools, llm):
    all_action_res = [list(action.keys())[0] for action in all_action_res]
    agent_scratchpad = base_llm_chain(llm, agent_scratchpad_prompt, query=query,
                                          all_action_res=all_action_res, thought=thought, tools=tools)

    # 防止出现一直重复规划已经执行步骤，死循环
    if len(all_action_res) > 5 or agent_scratchpad in all_action_res:
        print(f'开始生成重复步骤，或已执行 action 过多，判断结束了！重复步骤：{agent_scratchpad}')
        agent_scratchpad = 'no'
    return agent_scratchpad


def final_answer(query, query_rewrite, all_action_res, llm):
    answer = base_llm_chain(llm, final_answer_prompt, query=query,
                            query_rewrite=query_rewrite, all_action_res=all_action_res)
    return answer


if __name__ == '__main__':
    # llm
    llm_flashx = zhipu_glm_4(model_name='glm-4-flashx', temperature=0.1)
    llm_flash = zhipu_glm_4(model_name='glm-4-flash', temperature=0.1)
    llm_air = zhipu_glm_4(model_name='glm-4-air', temperature=0.1)

    # 问题
    query = """今天我遇到了一个身高比较高的小伙子，长得像钱七，还有他跟他身高差不多的兄弟李四，他们提到了大模型，
    但我不清楚大模型是什么。"""

    # query = """今天我遇到了一个身高比较高的小伙子，长得像钱七，还有他跟他身高差不多的兄弟李四，不知道他们多高，他们提到了大模型，
    #     但我不清楚大模型是什么。"""

    # 回答
    answer = agent(query, llm_air, 3)
    print(f'最终答案：\n{answer}')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
