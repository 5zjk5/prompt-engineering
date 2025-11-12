import asyncio
import aiohttp
import os
from logs.logger import define_log_level


async def fetch(session, topic, index, total, logger):
    # url = 'http://10.176.238.83:7396/api/deep_search'
    url = 'http://localhost:7396/api/deep_search'
    logger.info(f'ip:{url}')
    logger.info(f'【处理中】第 {index + 1}/{total} 条数据: {topic}')
    for i in range(3):  # 3 次机会
        try:
            async with session.post(url, json={"topic": topic, 'lang': 'en'}) as response:
                if response.status == 200:
                    result = await response.text()
                    if eval(result)['status'] == 200:
                        logger.info(f'✅ 完成 第 {index + 1} 条: {topic} | 响应长度: {len(result)}，{result[:50]}...')
                        break
                    else:
                        logger.error(f'❌ 完成 第 {index + 1} 条: {topic} | 响应长度: {len(result)}，{result[:50]}...')
                else:
                    logger.error(f'❌ 第 {index + 1} 条: {topic} 请求失败，{response.text()[:50]}...')
        except Exception as e:
            logger.error(f'⚠️ 第 {index + 1} 条: {topic} 请求失败，出错: {str(e)}')
            pass


async def worker(session, topic, index, total, semaphore, logger):
    async with semaphore:
        await fetch(session, topic, index, total, logger)


async def main(topics, max_concurrent=5):
    # 初始化日志
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger, log_name = define_log_level(project_root, "test_deepsearch_api")
    logger.info("开始测试deepsearch API...")
    
    total = len(topics)
    semaphore = asyncio.Semaphore(max_concurrent)  # 控制最大并发数量
    async with aiohttp.ClientSession() as session:
        tasks = [
            worker(session, topic, i, total, semaphore, logger)
            for i, topic in enumerate(topics)
        ]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    topics = ['最近医疗大健康有什么新动态，对创业者，个人有什么机遇？']
    asyncio.run(main(topics))
