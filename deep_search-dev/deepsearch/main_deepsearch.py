import asyncio
import traceback
import time
from api.llm_api import llm
from deepsearch.utils.utils import formulate_query, summarize_crawl_res, final_summary
from deepsearch.utils.parse_data import save_deepsearch_data
from deepsearch.prompt.prompt_lang import summary_text_prompt
from deepsearch.main_search import SearchCrawl


class DeepSearch():

    def __init__(self, topic, project_root, logger, max_epohs=5, cancel_event=None):
        """
        Args:
            topic: 主题
            project_root: 项目根目录
            logger: 日志
            max_epohs: 最大迭代次数
            summary_search: 总结的搜索结果
            crawl_res_lst: 原始的搜索结果
            have_query: 保存已有拆解子 query
            have_query: 保存已有拆解子任务
            cancel_event: 任务取消事件
        """
        self.topic = topic
        self.project_root = project_root
        self.logger = logger
        self.max_epohs = max_epohs
        self.summary_search = []
        self.have_query = []
        self.crawl_res_lst = []
        self.cancel_event = cancel_event
        self.search_crawl = SearchCrawl(self.topic, [], self.summary_search, self.logger)

    async def run(self):
        """
        处理 deepsearch 主逻辑

        Returns:
            JSON 结果
        """
        self.logger.info(f"================开始================")
        self.logger.info(f"开始深度搜索, 深度搜索主题：{self.topic}")

        # 遍历 max_epohs 次
        try:
            for ephos in range(self.max_epohs):
                try:
                    start = time.time()
                    self.logger.info(f"开始第 {ephos + 1}/{self.max_epohs} 轮搜索")

                    # 拆解 topic，生成子 query 用于搜索
                    rewrite_query = await self.step_formulate_query(ephos)
                    if not rewrite_query:
                        self.logger.info(f"第 {ephos + 1}/{self.max_epohs} 轮 topic 拆解无结果，开始下一轮迭代！")
                        continue

                    # 搜索，选需要结果，爬取具体网页
                    crawl_res = await self.step_search_crawl(rewrite_query)
                    if not crawl_res:
                        self.logger.info(f"第 {ephos + 1}/{self.max_epohs} 轮搜索无结果，开始下一轮迭代！")
                        continue

                    # 爬取结果总结，并判断是否足够回答 topic
                    answer = await self.step_summarize_crawl_res(crawl_res)

                    # 一轮耗时
                    self.logger.info(f"第 {ephos + 1}/{self.max_epohs} 轮搜索耗时：{time.time() - start}s")

                    # 评估反思信息足够了就退出
                    if 'yes' in answer:
                        break
                except asyncio.CancelledError:
                    raise asyncio.CancelledError
                except Exception as e:
                    self.logger.error(traceback.format_exc())
                    self.logger.error(f"第 {ephos + 1}/{self.max_epohs} 轮搜索出错，开始下一轮迭代！")
                    continue

            # 将所有总结额度网页内容合并起来做最后的总结
            summary_text = await self.step_final_summary()

            # 保存数据
            self.step_save_deepsearch_data(summary_text, locals().get('ephos', 0))

            self.logger.info(f'总共进行了 {locals().get("ephos", 0) + 1} 轮深度搜索！')
            self.logger.info(f'topic: {self.topic}')
            self.logger.info(f"================deepsearch 结束================")
            return {
                "status": "success",
                "topic": self.topic,
                "have_query": self.have_query,
                "summary_search": self.summary_search,
                "iter_num": locals().get("ephos", 0) + 1,
                "deepsearch_summary_text": summary_text
            }
        except asyncio.CancelledError:
            self.logger.warning(f'接收到取消任务信号，停止任务！')
            llm.cancel_request()
            raise
        finally:
            self.logger.warning(f'任务结束，搜索爬虫停止！')

    def watch_cancel_event(self):
        """
        监听取消事件，用于调用搜索，llm 之前
        """
        if self.cancel_event and self.cancel_event.is_set():
            self.logger.info("收到取消请求，开始任务取消！！！")
            raise asyncio.CancelledError()

    async def step_formulate_query(self, ephos):
        """
        step1 拆解 query
        """
        # 检查取消信号
        self.watch_cancel_event()

        tmp_start_time = time.time()
        rewrite_query = await formulate_query(self.topic, self.have_query, self.summary_search, self.logger)

        # 如果为第一轮把原始 topic 加入去搜索
        if ephos == 0:
            rewrite_query.append(self.topic)
        self.have_query.extend(rewrite_query)
        self.logger.info(f'拆解 topic，生成子 query 用于搜索耗时：{time.time() - tmp_start_time}s')
        return rewrite_query

    async def step_search_crawl(self, rewrite_query):
        """
        step2 搜索爬取结果
        """
        # 在调用搜索之前添加取消检查
        self.watch_cancel_event()

        # 更新 SearchCrawl 实例的查询和总结信息
        self.search_crawl.rewrite_query = rewrite_query
        self.search_crawl.summary_search = self.summary_search
        
        # 调用搜索，大模型选相关结果，爬取接口
        crawl_res = await self.search_crawl.run()
        self.crawl_res_lst.extend(crawl_res)
        return crawl_res

    async def step_summarize_crawl_res(self, crawl_res):
        """
        step3 爬取结果总结，并判断是否足够回答 topic
        """
        # 在调用LLM之前添加取消检查
        self.watch_cancel_event()

        # 对网页内容进行总结，判断是否能满足 topic
        tmp_start_time = time.time()
        answer, summary = await summarize_crawl_res(crawl_res, self.topic, self.summary_search, self.logger)
        self.summary_search.append(summary)
        self.logger.info(f'对网页内容进行总结，判断是否能满足 topic 耗时：{time.time() - tmp_start_time}s')
        return answer

    async def step_final_summary(self):
        """
        step4 所有搜索总结的结果用于最后总结，输出需要的结果
        """
        # 在调用LLM之前添加取消检查
        self.watch_cancel_event()

        tmp_start_time = time.time()
        if self.summary_search:
            summary_text = await final_summary(self.topic, self.summary_search, self.logger)
        else:
            summary_text = summary_text_prompt
        self.logger.info(f"最后总结耗时：{time.time() - tmp_start_time}s")
        return summary_text

    def step_save_deepsearch_data(self, summary_text, ephos):
        """
        保存数据，用于评估，分析等
        """
        tmp_start_time = time.time()
        save_deepsearch_data(self.topic, self.have_query, self.summary_search, summary_text, ephos + 1,
                             self.project_root, self.crawl_res_lst, self.logger, 'deep_search')
        self.logger.info(f"保存数据耗时：{time.time() - tmp_start_time}s")
