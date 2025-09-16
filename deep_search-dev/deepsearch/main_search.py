import re
import time
from deepsearch.prompt.prompt_lang import related_url_prompt
from api.llm_api import llm
from api.search_api import SearchAPI
from api.crawler_api import CrawlerAPI


class SearchCrawl():

    def __init__(self, topic, rewrite_query, summary_search, logger):
        """
        Args:
            topic: 主题
            logger: 日志
            rewrite_query: 子主题
            query_type: 子主题对应搜索时间范围
            summary_search: 总结的搜索结果
        """
        self.origin_query = topic
        self.rewrite_query = rewrite_query
        self.logger = logger
        self.summary_search = summary_search
        self.all_searched_urls = []  # 保存所有搜索到的URL
        self.selected_urls = []  # 保存已经挑选过的URL

    async def run(self):
        """
        1、搜索
        2、模型选出最适合的 url
        3、爬取具体内容

        Returns:
            爬取结果的列表
        """
        self.logger.info(f'开始搜索爬取...')

        # 搜索，返回url、标题、摘要、评分
        tmp_start_time = time.time()
        self.logger.info(
            f'开始调用搜索接口...\ntopic: {self.origin_query}\nrewrite_query: {self.rewrite_query}')
        
        # 创建SearchAPI实例并调用搜索接口
        search_api = SearchAPI(logger=self.logger)
        search_result = search_api.search(self.rewrite_query)
        self.logger.info(f'搜索接口调用工作流: {search_result.get('debug_url', '')}')
        
        if search_result.get("msg") == "success":
            serach_res_list = search_result.get("results", [])
        else:
            self.logger.error(f'搜索接口调用失败: {search_result.get("msg", "")}')
            serach_res_list = [] 
        if len(serach_res_list) == 0:
            self.logger.warning(f'共搜索到 0 条结果...')
            return []
        else:
            self.logger.info(f'共搜索到 {len(serach_res_list)} 条结果...')
        self.logger.info(f'调用搜索接口耗时：{time.time() - tmp_start_time}s')

        # 将新搜索到的URL添加到all_searched_urls列表中
        current_search_urls = [search.get("url", "") for search in serach_res_list]
        self.all_searched_urls.extend(current_search_urls)
        self.logger.info(f'当前总搜索URL数量: {len(self.all_searched_urls)}')

        # 根据搜索结果，用大模型进行url挑选
        tmp_start_time = time.time()
        self.logger.info(f'开始进行 url 筛选...')
        to_fetch_urls = await self.select_related_url(serach_res_list, self.logger)
        self.logger.info(f'共挑出 {len(to_fetch_urls)} 个需要的 url: {to_fetch_urls}')
        self.logger.info(f'调用大模型筛选 url 耗时：{time.time() - tmp_start_time}s')

        # 爬取url
        tmp_start_time = time.time()
        self.logger.info(f'开始爬取 url...')
        
        # 使用CrawlerAPI爬取URL
        async with CrawlerAPI(logger=self.logger) as crawler:
            fetch_res = await crawler.crawl_urls(to_fetch_urls)
        
        self.logger.info(f'爬取完成...')
        self.logger.info(f'调用爬虫接口获取网页内容耗时：{time.time() - tmp_start_time}s')

        if not fetch_res:
            self.logger.warning(f'搜索爬取结果为空！')

        # 爬取结果文本合并
        crawl_res = [data.get("content", "").replace('\n', '').replace('\t', '') for data in fetch_res if data.get("content", "") != 'NA'] if fetch_res else []
        return crawl_res

    async def select_related_url(self, serach_res_list, logger):
        """
        选择与 topic 需要的链接

        Args:
            serach_res_list: 搜索结果
            logger: 日志

        Returns:
            选出结果后搜索结果原始列表
        """
        # 组装搜索结果给模型使用
        ori_urls = []  # 兜底
        text = ''
        url_map = {}
        
        # 从all_searched_urls中排除已经挑选过的URL
        available_urls = [url for url in self.all_searched_urls if url not in self.selected_urls]
        
        # 构建URL映射和文本
        for i, search in enumerate(serach_res_list, start=1):
            # 从搜索结果中提取信息
            summary = search.get("summary", "")
            title = search.get("title", "")
            url = search.get("url", "")
            
            # 只处理可用的URL
            if url in available_urls:
                # 将信息添加到映射和原始URL列表
                ori_urls.append(url)
                url_map[f'url_{i}'] = url
                text += f'摘要：{summary}\n标题：{title}\n链接：url_{i}\n'
                text += '==============================================================\n'
        
        logger.info(f'映射后链接：{url_map}')
        logger.info(f'可用链接数量: {len(available_urls)}')
        logger.info(f'已挑选链接数量: {len(self.selected_urls)}')

        # 选择
        prompt = related_url_prompt.format(text=text, topic=self.origin_query, summary_search=self.summary_search).strip()
        logger.info(f'选择相关的搜索结果 prompt:\n{prompt}')
        response = await llm.infer(prompt)
        logger.info(f'大模型选择需要的搜索结果结果：\n{response}')

        url_lst = re.findall(r'```python(.*?)```', str(response), flags=re.S)
        if url_lst:
            related_urls = eval(url_lst[0])
            related_urls = [url_map[url_] for url_ in related_urls if url_ in url_map]
            # 更新已挑选的URL列表
            self.selected_urls.extend(related_urls)
        else:
            logger.warning(f'解析结果失败，使用原始所有结果...')
            related_urls = ori_urls
            # 更新已挑选的URL列表
            self.selected_urls.extend(related_urls)

        return related_urls
