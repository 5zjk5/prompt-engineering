import os
import re
import asyncio
from prompt.img_create import img_create_prompt
from logs.logger import logger
from llm.modelscope_api import modelscope_api
from save_chart import chart_save_fold


class ImageCreate:

    def __init__(self, results):
        """
        初始化图表生成器
            Args:
                results: 维度分析结果的列表
        """
        self.results = results
        self.prompt = img_create_prompt

    async def run(self):
        # 创建多个异步任务
        tasks = [self.run_task(result) for result in self.results]

        # 并发执行所有任务
        charts_results = await asyncio.gather(*tasks)

        return charts_results

    async def run_task(self, result):
        analysis_name = result['results']['analysis_name']

        # 生成代码
        prompt = self.prompt.format(input=result)
        content = modelscope_api(prompt)
        code, save_path = parse_code(content, analysis_name)
        logger.info(f"分析维度：{analysis_name} 代码：\n{code}\n")

        # 执行代码，错误还有一次机会纠正
        for cnt in range(2):
            try:
                exec(code)
                logger.info(f"分析维度：{analysis_name} 生成图表成功，图表保存路径：{save_path}")
                return {'status': 'success', 'analysis_name': analysis_name, 'save_path': save_path, 'result': result}
            except Exception as e:
                logger.error(f"分析维度：{analysis_name} 执行代码出错：{e} 自动纠正中...")
                content = modelscope_api(f'以下pyecharts代码报错了，报错信息：{e}\n请根据报错信息，修改代码，并直接返回修改后完整可运行的代码，按照markdown格式返回。以下是错误的代码：\n{code}')
                code, save_path = parse_code(content, analysis_name)
                logger.warning(f"分析维度：{analysis_name} **纠正后**代码：\n{code}\n")
        return {'status': 'error', 'analysis_name': analysis_name, 'result': result}


def parse_code(content, analysis_name):
    code = re.findall(r'```python(.*?)```', content, re.S)
    if code:
        code = code[0]
        # save_path = os.path.join(chart_save_fold, f'{analysis_name}.html')
        # code += f"chart.render(r'{save_path}')"

        save_path = os.path.join(chart_save_fold, f'{analysis_name}.png')  # markdown 不支持绝对路径
        save_code = f"""from pyecharts.render import make_snapshot\nfrom snapshot_selenium import snapshot\nmake_snapshot(snapshot, chart.render(), "{save_path}")"""
        if save_code not in code:
            code += save_code

        return code, save_path
    else:
        return content, ''
