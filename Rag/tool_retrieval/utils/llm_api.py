import asyncio
import os
from openai import AsyncOpenAI
import logging


# 设置日志级别
# logging.getLogger("openai").setLevel(logging.ERROR)


class LLM():

    def __init__(self, logger=None):
        self.model = os.getenv('MODEL', 'glm-4.5-flash')
        self.client = AsyncOpenAI(
            api_key=os.getenv('API_KEY'),
            base_url=os.getenv('BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')
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
                raise Exception(f'llm fail: {str(e)}')
            finally:
                # 清除请求引用
                self.current_request = None

    def cancel_request(self):
        """取消当前请求"""
        if self.current_request and not self.current_request.done():
            self.current_request.cancel()
            return True
        return False
