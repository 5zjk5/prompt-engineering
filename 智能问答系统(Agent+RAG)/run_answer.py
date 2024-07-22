# coding:utf8
import warnings
import traceback
from utils.utils import read_jsonl, write_jsonl, classify_question
from llm.llm_glm import zhipu_glm_4
from llm.llm_tongyi import tongyi_qwen_turbo
from RAG.retriver_by_rule import retriver_by_rule
from agent.agent_execute import agent_execute


warnings.filterwarnings('ignore')
glm4 = zhipu_glm_4(temperature=0.1)
tongyi_turbo = tongyi_qwen_turbo(temperature=0.1)

debug = False


def get_answer(question):
    try:
        # 问题分类
        # classification = classify_question(question, glm4)
        classification = 'sql'  # todo
        print(f'分类:{classification}')

        # RAG
        if '招股' in classification:
            answer1 = retriver_by_rule(question, glm4)
            answer = answer1
        # Agent
        if 'sql' in classification:
            question = '如果得到了 sql 语句必须调用工具去执行，' + question
            answer2 = agent_execute(question, glm4, debug)
            answer = answer2
        # 混合
        if '招股' in classification and 'sql' in classification:
            answer = answer1 + answer2
        return answer
    except Exception as e:
        if debug:
            traceback.print_exc()
        return f'系统错误{e}'


if __name__ == '__main__':
    # 读取问题
    question_path = 'data/dataset/question.json'
    question_list = read_jsonl(question_path)
    question_list = question_list[500:]

    save_path = 'data/answer/submit_result.jsonl'
    content = []
    for index, row in enumerate(question_list):
        print(f'-------------- {index} / {len(question_list)} -------------------')
        id = row['id']
        question = row['question']
        print(f'当前id：{id} | 当前问题：{question}')

        # 存入列表
        answer = get_answer(question)
        print('answer:', answer, 'finish!')
        content.append({'id': id, 'question': question, 'answer': answer})

    # 保存
    write_jsonl(save_path, content)
