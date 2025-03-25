from logs.logger import logger
from memory.base import BaseMemory
from prompt.fc_prompt import system_prompt
from config.config import fc_llm, tools
from tool.base import tool_map


class FCAgent():

    def __init__(self):
        self.memory = BaseMemory()
        self.system_prompt = system_prompt
        self.memory.add_message({'role': 'system', 'content': self.system_prompt})

    def function_call(self, sub_task):
        """任务执行"""
        logger.info('🤟正在执行任务......')
        message = {'role': 'user', 'content': sub_task}
        self.memory.add_message(message)

        # 历史记忆
        messages = self.memory.get_all_messages()
        for message in messages:
            logger.info(f'function call history: {message}')

        # 怎么执行？
        step = fc_llm.infer_tool(messages, tools=tools)
        logger.info(f'function call response: {step}')

        # 是否调用工具？
        tool_calls = step.tool_calls
        if tool_calls:
            tool_names = [tool.function.name for tool in tool_calls]
            logger.info(f'🔨fc_agent select {len(tool_calls)} tools: {tool_names}')
            res_lst = []
            for tool in tool_calls:
                tool_name = tool.function.name
                logger.info(f'🔨fc_agent useing {tool_name}.....')
                if not tool_map.get(tool_name):
                    raise Exception(f'{tool_name} is not exist')
                try:
                    tool_res = tool_map[tool_name](**eval(tool.function.arguments))
                except Exception as err:
                    tool_res = err
                res = {'role': 'assistant', 'content': f'子任务`{sub_task}`的执行结果: {tool_res}'}
                res_lst.append(res)
                logger.info(f'🔨子任务`{sub_task}`的执行结果: {tool_res}')
        else:
            logger.info(f'🔨fc_agent not need tools')
            res_lst = [{'role': 'assistant', 'content': step.content}]

        # 记忆添加
        for res in res_lst:
            self.memory.add_message(res)

        logger.info(f'🔨当前子任务：{sub_task}')
        logger.info(f'🔨当前子任务执行结果：{res}')
        return res_lst
