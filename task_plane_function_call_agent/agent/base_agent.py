from logs.logger import logger
from config.config import max_steps, final_label
from agent.tp_agent import TPAgent
from agent.fc_agent import FCAgent
from prompt.tp_prompt import next_prompt


class TPFCAgent():
    def __init__(self):
        self.current_step = 0
        self.max_steps = max_steps
        self.final_label = final_label
        self.tp_agent = TPAgent()
        self.fc_agent = FCAgent()

    def run(self, prompt):
        cur_prompt = prompt
        while self.current_step <= self.max_steps:
            self.current_step += 1
            logger.info(f"Executing step {self.current_step}/{self.max_steps}")

            # task plan step
            step, sub_task = self.tp_agent.task_plan(cur_prompt)

            # 如果有最终回答，代表结束
            if self.final_label in step:
                final_answer = ''.join(step.split(self.final_label)[-1])
                logger.info(f"最终回答：{final_answer}")
                break

            # function call step
            fc_res_lst = self.fc_agent.function_call(sub_task)

            # 将执行结果添加到tp_agent的memory中，角色为 user
            for fc_res in fc_res_lst:
                fc_res = {'role': 'user', 'content': fc_res['content']}
                self.tp_agent.memory.add_message(fc_res)

            # 提示 tp agent 规划下一步
            cur_prompt = next_prompt

        if self.current_step > self.max_steps:
            logger.warning(f"执行到最大步骤，记忆清空........")
