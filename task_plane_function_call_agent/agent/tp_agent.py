import json
from logs.logger import logger
from memory.base import BaseMemory
from prompt.tp_prompt import system_prompt
from config.config import tp_llm


class TPAgent():

    def __init__(self):
        self.memory = BaseMemory()
        self.system_prompt = system_prompt
        self.memory.add_message({'role': 'system', 'content': self.system_prompt})

    def task_plan(self, prompt):
        """任务拆解"""
        logger.info('🤔正在思考进行任务拆解......')
        message = {'role': 'user', 'content': prompt}
        self.memory.add_message(message)

        # 历史记忆
        messages = self.memory.get_all_messages()
        for message in messages:
            logger.info(f'task plan history: {message}')

        # 子任务拆解
        step = tp_llm.infer(messages)
        logger.info(f'task plan response: {step}')
        step = step.strip('`json\n')
        step = self.del_err_final_answer(step)
        try:
            step = json.loads(step)
            thought = step.get('thought')
            sub_task = step.get('sub_task')
        except:
            thought = step.split('sub_task')[0].strip('\n :')
            sub_task = step.split('sub_task')[-1].strip('\n :')
        self.memory.add_message({'role': 'assistant', 'content': sub_task})

        logger.info(f'🤔思考：{thought}')
        logger.info(f'🤔拆解子任务：{sub_task}')
        return str(step), sub_task

    def del_err_final_answer(self, step):
        """子任务还有，但出现了 final answer 且为空，删除"""
        _del = ['"final_answer": ""', '"final_answer": "null"', '"final_answer": null']
        for _ in _del:
            step = step.replace(_, '')
        return step
