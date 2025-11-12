import asyncio
from playwright.async_api import async_playwright
import logging
from typing import List, Dict, Any


# 设置日志级别
logging.getLogger("playwright").setLevel(logging.ERROR)


class CrawlerAPI:
    def __init__(self, logger=None):
        self.browser = None
        self.context = None
        self.playwright = None
        self.logger = logger or logging.getLogger(__name__)
        
    async def init_browser(self):
        """初始化浏览器"""
        if not self.browser:
            try:
                self.playwright = await async_playwright().start()

                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    timeout=10000  # 添加浏览器启动超时
                )
                
                if self.browser:
                    self.context = await self.browser.new_context()
                else:
                    self.logger.error("浏览器启动失败")
            except Exception as e:
                self.logger.error(f"浏览器初始化出错: {str(e)}")
                self.browser = None
                self.context = None
                self.playwright = None
                # 重新抛出异常以便上层处理
                raise
            
    async def close_browser(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
    async def crawl_single_url(self, url: str) -> Dict[str, Any]:
        """
        爬取单个URL的内容
        
        Args:
            url (str): 要爬取的URL
            
        Returns:
            Dict[str, Any]: 包含url和content的字典
        """
        if not self.context:
            await self.init_browser()
            
        # 再次检查context是否初始化成功
        if not self.context:
            return {
                "url": url,
                "content": "浏览器初始化失败"
            }
            
        try:
            page = await self.context.new_page()
            # 设置更短的超时时间和更宽松的等待条件
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # 等待一小段时间确保页面加载
            await asyncio.sleep(1)
            
            # 获取页面文本内容（不包含HTML标签）
            content = await page.inner_text("body")
            
            # 关闭页面
            await page.close()
            
            return {
                "url": url,
                "content": content if content else "无法获取页面文本内容"
            }
        except asyncio.TimeoutError:
            logging.error(f"爬取URL {url} 超时")
            return {
                "url": url,
                "content": "爬取超时，可能是网站加载太慢或无法访问"
            }
        except Exception as e:
            logging.error(f"爬取URL {url} 时出错: {str(e)}")
            return {
                "url": url,
                "content": f"爬取失败: {str(e)}"
            }
            
    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        并行爬取多个URL的内容
        
        Args:
            urls (List[str]): 要爬取的URL列表
            
        Returns:
            List[Dict[str, Any]]: 包含每个URL的url和content的字典列表
        """
        if not self.context:
            await self.init_browser()
            
        # 创建任务列表
        tasks = [self.crawl_single_url(url) for url in urls]
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        formatted_results = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"爬取任务出错: {str(result)}")
                continue
            formatted_results.append(result)
            
        return formatted_results
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_browser()
