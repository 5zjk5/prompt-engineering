import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging


# 设置日志级别
logging.getLogger("openai").setLevel(logging.ERROR)

# 加载环境变量
load_dotenv()


class LLM():

    def __init__(self, logger=None):
        self.model = os.getenv('GLM_MODEL', 'glm-4.5-flash')
        self.client = AsyncOpenAI(
            api_key=os.getenv('GLM_API_KEY'),
            base_url=os.getenv('GLM_BASE_URL', 'https://openai.deepseek.cn/v1')
        )
        self.current_request = None
        self.logger = logger or logging.getLogger(__name__)

    async def infer(self, prompt, enable_thinking=False, temperature=0.7):
        # 确保打印的 self.model 不是元组
        self.logger.info(f'调用模型：{self.model}......')
        
        # 创建可中断的请求
        async with asyncio.TaskGroup() as tg:
            request_task = tg.create_task(self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={
                    'thinking': {
                        "type": "enabled" if enable_thinking else "disabled"
                    }
                },
                temperature=temperature
            ))

            # 保存当前请求的引用
            self.current_request = request_task

            try:
                response = await request_task
                content = response.choices[0].message.content
                return content
            except Exception as e:
                if 'You exceeded your current quota, please check your plan and billing details.' in str(e):
                    content = 'You exceeded your current quota, please check your plan and billing details.'
                elif '413 Request Entity Too Large' in str(e):
                    content = '413 Request Entity Too Large.'
                else:
                    raise Exception(f'llm fail: Too many requests or Other error.')
                return content
            finally:
                # 清除请求引用
                self.current_request = None

    def cancel_request(self):
        """取消当前请求"""
        if self.current_request and not self.current_request.done():
            self.current_request.cancel()
            return True
        return False


llm = LLM()
