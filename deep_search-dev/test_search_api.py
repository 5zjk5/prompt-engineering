import asyncio
import os
from dotenv import load_dotenv
from api.search_api import SearchAPI
from logs.logger import define_log_level


# 加载环境变量
load_dotenv()


async def test_search_api():
    """测试搜索API"""
    # 初始化日志
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger, log_name = define_log_level(project_root, "test_search_api")
    logger.info("开始测试搜索API...")
    
    # 创建搜索API实例
    search_api = SearchAPI(logger)
    
    # 测试搜索
    user_input = ["langchain", "天气预报"]
    logger.info(f"搜索关键词: {user_input}")
    
    try:
        # 执行搜索
        response = search_api.search(user_input)
        logger.info("搜索结果:")
        
        # 提取debug_url和结果列表
        debug_url = response.get("debug_url", "")
        results = response.get("results", [])
        
        # 打印debug_url
        logger.info(f"Debug URL: {debug_url}")
        
        # 检查结果是否为空
        if not results:
            logger.warning("搜索结果为空")
            logger.error("搜索API测试失败!")
        else:
            # 打印每个搜索结果
            for i, result in enumerate(results, 1):
                logger.info(f"\n结果 {i}:")
                logger.info(f"  网站名称: {result['sitename']}")
                logger.info(f"  标题: {result['title']}")
                logger.info(f"  摘要: {result['summary']}")
                logger.info(f"  URL: {result['url']}")
            
            logger.info("搜索API测试成功!")
            
    except Exception as e:
        logger.error(f"搜索API测试失败: {e}")

async def test_multiple_searches():
    """测试多个搜索请求"""
    # 初始化日志
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger, log_name = define_log_level(project_root, "test_multiple_searches")
    logger.info("\n开始测试多个搜索请求...")
    
    # 创建搜索API实例
    search_api = SearchAPI(logger)
    
    # 测试不同的搜索关键词
    test_cases = [
        ["人工智能", "应用"],
        ["Python", "编程"],
        ["机器学习", "算法"]
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        logger.info(f"\n测试用例 {i}: {user_input}")
        try:
            response = search_api.search(user_input)
            
            # 提取debug_url和结果列表
            debug_url = response.get("debug_url", "")
            results = response.get("results", [])
            
            # 打印debug_url
            logger.info(f"Debug URL: {debug_url}")
            
            # 检查结果是否为空
            if not results:
                logger.warning(f"搜索结果 {i} 为空")
            else:
                logger.info(f"搜索结果 {i} 共找到 {len(results)} 条结果:")
                # 打印每个搜索结果的标题和URL
                for j, result in enumerate(results, 1):
                    logger.info(f"  {j}. {result['title']} - {result['url']}")
                    
        except Exception as e:
            logger.error(f"搜索请求 {i} 失败: {e}")

async def main():
    """主测试函数"""
    print("开始测试搜索API...")
    
    # 测试单个搜索请求
    await test_search_api()
    
    # 测试多个搜索请求
    await test_multiple_searches()
    
    print("\n所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())