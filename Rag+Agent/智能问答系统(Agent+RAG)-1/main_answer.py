import warnings
import traceback
import time
from llm.llm_glm import zhipu_glm_4
from utils.utils import read_jsonl, write_jsonl, classify_question, log_handle, calc_token, create_write_jsonl
from RAG.retriver_by_rule import retriver_by_rule
from agent.agent_execute import agent_execute, comprehend_db_table


warnings.filterwarnings('ignore')

# llm
llm_flashx = zhipu_glm_4(model_name='glm-4-flashx', temperature=0.1)
llm_flash = zhipu_glm_4(model_name='glm-4-flash', temperature=0.1)
llm_air = zhipu_glm_4(model_name='glm-4-air', temperature=0.1)

print = log_handle()

# 理解数据表
db_table_memory = comprehend_db_table(llm_air, print)


def get_answer(question):
    try:
        # 问题分类
        classification = classify_question(question, llm_flash, print)
        print(f'分类:{classification}')

        answer, answer1, answer2 = '', '', ''
        # RAG
        if '招股' in classification:
            answer1 = retriver_by_rule(question, llm_flash, print)
            answer = answer1
        # Agent
        if 'sql' in classification:
            answer2 = agent_execute(question, llm_air, db_table_memory, print)
            answer = answer2
        # 混合
        if '招股' in classification and 'sql' in classification:
            answer = answer1 + answer2

        return answer
    except Exception as e:
        print(traceback.print_exc())
        print(f'系统错误 error:{e}')
        return f'系统错误{e}'


if __name__ == '__main__':
    start_time = time.time()

    # 读取问题
    question_path = 'data/dataset/question.json'
    question_list = read_jsonl(question_path)
    question_list = question_list[873:]

    save_path = 'data/answer/submit_result_1011.jsonl'
    create_write_jsonl(save_path)

    for index, row in enumerate(question_list):
        content = []
        cur_start_time = time.time()

        print('==================================================================')
        print(f'-------------- {index} / {len(question_list)} -------------------')
        id = row['id']
        question = row['question']
        print(f'当前id：{id}')
        print(f'当前问题：{question}')

        # 存入列表，保存
        answer = get_answer(question)
        print('answer:', answer, 'finish!')
        content.append({'id': id, 'question': question, 'answer': answer})
        write_jsonl(save_path, content)

        cue_end = time.time()
        print(f'当前问题处理时间：{cue_end - cur_start_time}s')
        print('==================================================================')

        # 计算当前问题总共 token
        calc_token(print)

    end_time = time.time()
    print(f'总耗时：{end_time - start_time}s')
