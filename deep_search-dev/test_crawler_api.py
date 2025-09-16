import asyncio
import sys
import os
import time
import logging

# 添加项目根目录到Python路径
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.crawler_api import CrawlerAPI
from logs.logger import define_log_level


async def test_crawler_api():
    """测试爬虫API功能"""
    # 初始化日志
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger, log_name = define_log_level(project_root, "test_crawler_api")
    # 测试URL列表 - 使用更简单、更可能快速加载的URL
    test_urls = [
        "https://www.baidu.com",
        # "https://blog.csdn.net/zjkpy_5/category_9516137.html?spm=1001.2014.3001.5482",
        "https://www.msn.cn/zh-cn/news/other/%E5%AE%98%E6%96%B9%E9%80%9A%E6%8A%A5-%E5%A5%B3%E5%AD%90%E8%AF%AF%E8%B8%A9%E6%B0%A2%E6%B0%9F%E9%85%B8%E4%B8%AD%E6%AF%92-%E6%8A%A2%E6%95%91%E6%97%A0%E6%95%88%E4%B8%8D%E5%B9%B8%E8%BA%AB%E4%BA%A1/ar-AA1MBYd6?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=7",
        "https://www.msn.cn/zh-cn/news/other/%E4%BA%8B%E5%8F%91%E4%B8%8A%E6%B5%B7%E8%99%B9%E6%A1%A5%E7%AB%99-%E7%94%B7%E5%AD%90%E8%87%AA%E7%A7%B0%E7%89%A9%E5%93%81%E4%B8%A2%E5%A4%B1-%E9%9D%A2%E5%AF%B9%E8%AD%A6%E5%AF%9F%E5%8D%B4%E6%85%8C%E4%BA%86/ar-AA1MC0tt?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=12",
        "https://www.msn.cn/zh-cn/news/other/%E9%BB%84%E9%9C%84%E4%BA%91%E5%A4%A7%E5%8F%98%E6%A0%B7-%E7%BD%91%E5%8F%8B%E6%83%8A%E5%8F%B9-%E6%9E%9C%E7%84%B6%E9%92%B1%E8%83%BD%E5%85%BB%E4%BA%BA/ar-AA1MxZtq?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=18"
    ]
    
    logger.info("开始测试爬虫API...")
    logger.info(f"测试URL列表: {test_urls}")
    
    start_time = time.time()
    
    try:
        # 使用异步上下文管理器
        async with CrawlerAPI(logger=logger) as crawler:
            # 爬取URL内容
            logger.info("开始爬取URL内容...")
            results = await crawler.crawl_urls(test_urls)
            
            end_time = time.time()
            logger.info(f"爬取完成，总耗时: {end_time - start_time:.2f}秒")
            
            # 打印结果
            logger.info("爬取结果:")
            for i, result in enumerate(results, 1):
                logger.info(f"\n结果 {i}:")
                logger.info(f"URL: {result['url']}")
                # 只打印前100个字符的内容预览
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                logger.info(f"内容预览: {content_preview}")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("测试完成")


if __name__ == "__main__":
    asyncio.run(test_crawler_api())
    