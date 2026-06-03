import os
import time
import traceback
import asyncio
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from prompts.today_news import (
    search_url_create,
    select_link_prompt,
    compress_content_prompt,
    summary_today_prompt,
    analyze_last_week_prompt,
    filter_date_prompt,
)
from llm.ChatOpenAIModel_LangChian import ChatOpenAIModel
from utils.llm_generation import call_llm_with_retry
from tools.search import duckduckgo_search, huoshan_search
from tools.fetch import coze_fetch, jina_fetch


class TodayNews:
    def __init__(self, logger):
        self.logger = logger
        self.search_iter_num = 3  # 搜索query迭代次数
        self.confidence_threshold = 0.7  # 置信度阈值
        self.compress_num = 50  # 压缩批次大小
        self.fetch_url_batch = 50  # fetch url 批次大小

        # 大模型配置
        extra_body = json.loads(os.getenv("EXTRA_BODY", "{}"))
        self.llm = ChatOpenAIModel(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_API_URL"),
            extra_body=extra_body,
            model=os.getenv("LLM_MODEL"),
            timeout=180,
        )

    async def get_today_news(self):
        """获取今日新闻"""
        self.logger.info("获取今日新闻")

        # 单独筛选处理 url 源，获取总结
        reference_summaries = await self.fetch_reference_url()

        # 生成 query
        querys = await self.generate_query()

        # 搜索 query 获得链接
        query_link = await self.search_query(querys)

        # 选取 query 搜索获得的链接
        select_query_link = await self.select_link(query_link)
        select_query_link = [item["url"] for item in select_query_link]

        # fetch query 获得的链接
        all_content = await self.fetch_links(select_query_link)

        # 总结压缩网页内容
        compressed_results = await self.compress_content(all_content)

        # 总结今天的结果
        today_results = await self.summary_today(compressed_results, reference_summaries)

        # 保存到数据库
        await self.save_to_db(today_results)

        # 读取过去一周新闻
        last_week_news = await self.read_last_week_news()

        # 最后分析
        final_result = await self.analyze_last_week_news(today_results, last_week_news)

        return final_result

    async def fetch_reference_url(self):
        """获取 reference 下的新闻URL，过滤并总结当天或昨天的内容"""
        time_start = time.time()
        self.logger.info("处理 reference 下的新闻URL....")

        # 读取 reference 下的news-url.txt
        news_urls_path = Path("reference") / "news-url.txt"
        with open(news_urls_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        self.logger.info(f"已读取 URL 文件: {news_urls_path}，共 {len(links)} 个链接")

        # 获取 url 内容
        fetch_content = await self.fetch_links(links)

        # 判断哪些是24小时以内的，或者一天前的
        content = await self.filter_by_date(fetch_content)

        return "\n===============\n".join(content)

    async def filter_by_date(self, all_content):
        """过滤网页内容，只保留当天或一天前的内容，并输出总结"""
        time_start = time.time()
        self.logger.info("过滤 reference url 网页内容，判断日期....")

        now = datetime.now()
        today_date = now.strftime("%Y/%m/%d")
        yesterday_date = (now - timedelta(days=1)).strftime("%Y/%m/%d")
        old_date_example = (now - timedelta(days=2)).strftime("%Y/%m/%d")
        self.logger.info(f"今天日期: {today_date}，昨天日期: {yesterday_date}")

        all_summaries = []
        batch_size = 50

        for i in range(0, len(all_content), batch_size):
            batch = all_content[i : i + batch_size]
            total_batches = (len(all_content) + batch_size - 1) // batch_size
            current_batch = i // batch_size + 1
            processed = i + len(batch)
            self.logger.info(
                f"日期过滤批次 {current_batch}/{total_batches}: {len(batch)} 个网页 (进度: {processed}/{len(all_content)})"
            )

            text = ""
            for idx, item in enumerate(batch, start=1):
                content = item.get("content", "")
                url = item.get("url", "")
                text += f"网页{idx}：\nURL: {url}\n内容：\n{content}\n"
                text += "====================\n"

            prompt = filter_date_prompt.format(
                today_date=today_date,
                yesterday_date=yesterday_date,
                old_date_example=old_date_example,
                text=text,
            ).strip()
            self.logger.info(
                f"reference url 网页日期过滤 prompt 长度: {len(prompt)} 字符"
            )
            response = call_llm_with_retry(self.llm, prompt, self.logger)
            self.logger.info(
                f"reference url 网页日期过滤过滤结果：\n{str(response.content)}"
            )

            summary_text = str(response.content).strip()
            if summary_text and "暂无符合条件的新闻内容" not in summary_text:
                filtered_summary = self._post_filter_by_date(
                    summary_text, today_date, yesterday_date
                )
                if filtered_summary:
                    all_summaries.append(filtered_summary)
                    self.logger.info(f"批次 {current_batch} 生成总结成功")
                else:
                    self.logger.info(f"批次 {current_batch} 后处理后无符合条件的新闻")
            else:
                self.logger.info(f"批次 {current_batch} 无符合条件的新闻")

        end_time = time.time()
        self.logger.info(
            f"reference url 网页日期过滤耗时: {end_time - time_start} 秒，共生成 {len(all_summaries)} 个总结"
        )
        return all_summaries

    def _post_filter_by_date(self, summary_text, today_date, yesterday_date):
        """后处理：解析字符串并过滤掉日期不是今天或昨天的新闻"""
        valid_dates = {today_date, yesterday_date}

        if "暂无符合条件的新闻内容" in summary_text:
            return ""

        news_blocks = summary_text.split("===")

        valid_news = []
        for block in news_blocks:
            block = block.strip()
            if not block:
                continue

            source_match = re.search(r"【来源】(.+?)(?=\n|【日期】)", block)
            date_match = re.search(r"【日期】(\d{4}/\d{2}/\d{2})", block)
            content_match = re.search(r"【内容】(.+)$", block, flags=re.S)

            if not date_match:
                self.logger.info(f"后处理过滤掉无日期新闻")
                continue

            news_date = date_match.group(1)
            if news_date not in valid_dates:
                self.logger.info(f"后处理过滤掉过时新闻，日期: {news_date}")
                continue

            source = source_match.group(1).strip() if source_match else "未知"
            content = content_match.group(1).strip() if content_match else ""

            valid_news.append({"source": source, "date": news_date, "content": content})

        if not valid_news:
            return ""

        result_lines = ["## 今日新闻摘要"]
        for idx, news in enumerate(valid_news, start=1):
            result_lines.append(f"\n### 新闻{idx}")
            result_lines.append(f"- **来源**：{news['source']}")
            result_lines.append(f"- **日期**：{news['date']}")
            result_lines.append(f"- **内容**：{news['content']}")

        return "\n".join(result_lines)

    async def generate_querys(self, query_templates, date_range, existing=""):
        """生成查询"""
        time_start = time.time()
        self.logger.info("生成查询....")

        prompt = search_url_create.format(
            date_range=date_range,
            query_templates=query_templates,
            existing=existing,
        )
        self.logger.info(f"生成查询 prompt:\n{prompt}")
        response = call_llm_with_retry(self.llm, prompt, self.logger)
        self.logger.info(f"模型生成查询结果:\n{str(response.content)}")

        # 解析模型回复，提取 QUERY
        querys = []
        lines = response.content.strip().split("\n")
        for line in lines:
            line = line.strip().replace("date_range", date_range)
            if line.startswith("QUERY:"):
                query = line[6:].strip()
                if query and query not in querys:
                    querys.append(query)

        self.logger.info(f"本次生成 {len(querys)} 个查询")
        end_time = time.time()
        self.logger.info(f"生成查询耗时: {end_time - time_start} 秒")
        return querys

    async def generate_query(self):
        """迭代生成查询"""
        time_start = time.time()
        self.logger.info("迭代生成查询....")

        # 读取 reference 下的news-query.txt
        news_query_path = Path("reference") / "news-query.txt"
        with open(news_query_path, "r", encoding="utf-8") as f:
            query_templates = f.read()
        self.logger.info(f"已读取查询模版文件: {news_query_path}")

        # 计算日期范围
        now = datetime.now()
        start_time = now - timedelta(hours=24)
        date_range = f"{start_time.strftime('%Y/%m/%d %H:%M')} - {now.strftime('%Y/%m/%d %H:%M')}"

        # 迭代生成查询
        existing = ""
        all_querys = []
        self.logger.info(f"开始迭代生成查询，共 {self.search_iter_num} 次")
        for i in range(self.search_iter_num):
            try:
                gen_querys = await self.generate_querys(
                    query_templates, date_range, existing
                )

                # 拼接所有已生成的查询
                if existing:
                    existing += "\n\n" + "\n".join([f"QUERY: {q}" for q in gen_querys])
                else:
                    existing = "\n".join([f"QUERY: {q}" for q in gen_querys])

                all_querys.extend(gen_querys)
                self.logger.info(
                    f"第 {i+1} 次生成查询完成，当前共 {len(all_querys)} 个查询"
                )
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error(f"第 {i+1} 次生成查询调用失败: {str(e)}")
                continue

        all_querys = list(set(all_querys))
        self.logger.info(f"共生成 {len(all_querys)} 个去重后的查询")
        end_time = time.time()
        self.logger.info(f"迭代生成查询耗时: {end_time - time_start} 秒")
        return all_querys

    async def search_query(self, querys):
        """搜索查询，分批并发，交替搜索，减缓压力"""
        time_start = time.time()
        self.logger.info("query 搜索查询....")
        all_results = []

        batch_size = 10
        total_batches = (len(querys) + batch_size - 1) // batch_size

        for i in range(0, len(querys), batch_size):
            batch = querys[i : i + batch_size]
            batch_num = i // batch_size + 1

            self.logger.info(
                f"DuckDuckGo 批次 {batch_num}/{total_batches}: 处理 {len(batch)} 个查询 (进度: {min(i + batch_size, len(querys))}/{len(querys)})"
            )
            duckduckgo_tasks = [
                # asyncio.to_thread(duckduckgo_search, query) for query in batch
                asyncio.to_thread(huoshan_search, query, count=20) for query in batch
            ]
            duckduckgo_results = await asyncio.gather(
                *duckduckgo_tasks, return_exceptions=True
            )
            for result in duckduckgo_results:
                if not isinstance(result, Exception) and result:
                    all_results.extend(result)
                if isinstance(result, Exception):
                    self.logger.error(f"duckduckgo_search 调用失败: {str(result)}")

            time.sleep(5)

        # 去重
        self.logger.info(f"去重前搜索结果: {len(all_results)} 条")
        seen_urls = set()
        unique_results = []
        for item in all_results:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(item)
        all_results = unique_results
        self.logger.info(f"去重后搜索结果: {len(all_results)} 条")

        end_time = time.time()
        self.logger.info(f"部分结果：{all_results}")
        self.logger.info(
            f"搜索查询耗时: {end_time - time_start} 秒，共获取 {len(all_results)} 条结果"
        )
        return all_results

    async def select_link(self, query_link):
        """选取 query 搜索获得的链接"""
        time_start = time.time()
        self.logger.info("query 搜索结果选取链接....")

        batch_size = 50
        all_selected_urls = []
        all_url_id_to_original = {}

        global_idx = 1

        for batch_idx in range(0, len(query_link), batch_size):
            batch = query_link[batch_idx : batch_idx + batch_size]
            self.logger.info(
                f"置信度打分处理批次 {batch_idx // batch_size + 1}: {len(batch)} 个搜索结果"
            )

            url_map = {}
            url_id_to_original = {}
            text = ""

            for i, search in enumerate(batch, start=1):
                summary = search.get("summary", "")
                title = search.get("title", "")
                url = search.get("url", "")
                url_id = f"url_{global_idx}"
                global_idx += 1

                url_map[url_id] = url
                url_id_to_original[url_id] = search
                text += f"摘要：{summary}\n标题：{title}\n链接：{url_id}\n"
                text += (
                    "==============================================================\n"
                )

            self.logger.info(f"映射后链接：{url_map}")
            self.logger.info(f"搜索结果数量: {len(batch)}")

            # 动态生成日期范围
            now = datetime.now()
            start_time = now - timedelta(hours=24)
            today_date = now.strftime("%Y%m%d")
            date_range = (
                f"{start_time.strftime('%Y/%m/%d')} - {now.strftime('%Y/%m/%d')}"
            )

            prompt = select_link_prompt.format(
                text=text, today_date=today_date, date_range=date_range
            ).strip()
            self.logger.info(f"选择相关的搜索结果 prompt:\n{prompt}")
            response = call_llm_with_retry(self.llm, prompt, self.logger)
            self.logger.info(
                f"大模型对搜索结果置信度打分批次 {batch_idx}/{len(query_link)} 个打分结果：\n{response.content}"
            )

            json_match = re.search(
                r"```json(.*?)```", str(response.content), flags=re.S
            )
            if json_match:
                try:
                    selected_results = json.loads(json_match.group(1).strip())
                    selected_urls = []
                    for item in selected_results:
                        url_id = item.get("id", "")
                        if url_id in url_map:
                            confidence = item.get("confidence", 0.0)
                            try:
                                confidence = float(confidence)
                            except (ValueError, TypeError):
                                confidence = 0.0
                            selected_urls.append(
                                {
                                    "url_id": url_id,
                                    "url": url_map[url_id],
                                    "confidence": confidence,
                                    "reason": item.get("reason", ""),
                                }
                            )
                    self.logger.info(f"成功解析结果，共 {len(selected_urls)} 个链接")
                except Exception as e:
                    self.logger.error(f"解析 JSON 失败: {str(e)}，使用原始所有结果")
                    selected_urls = [
                        {"url_id": url_id, "url": url, "confidence": 1.0}
                        for url_id, url in url_map.items()
                    ]
            else:
                self.logger.warning(
                    f"未找到 JSON 格式结果，使用原始所有结果，所有置信度为 1.0"
                )
                selected_urls = [
                    {"url_id": url_id, "url": url, "confidence": 1.0}
                    for url_id, url in url_map.items()
                ]

            all_selected_urls.extend(selected_urls)
            all_url_id_to_original.update(url_id_to_original)

        end_time = time.time()
        self.logger.info(
            f"链接置信度打分耗时: {end_time - time_start} 秒，共打分 {len(all_selected_urls)} 条"
        )

        self.logger.info(f"过滤前: {len(all_selected_urls)} 条链接")
        filtered_urls = [
            item
            for item in all_selected_urls
            if item.get("confidence", 0.0) >= self.confidence_threshold
        ]
        self.logger.info(
            f"过滤后（阈值 {self.confidence_threshold}）: {len(filtered_urls)} 条链接"
        )

        final_results = []
        for item in filtered_urls:
            url_id = item.get("url_id", "")
            if url_id in all_url_id_to_original:
                original = all_url_id_to_original[url_id].copy()
                original["confidence"] = item.get("confidence", 0.0)
                original["reason"] = item.get("reason", "")
                final_results.append(original)

        return final_results

    async def fetch_links(self, links):
        """获取所有链接"""
        time_start = time.time()
        self.logger.info("获取所有链接对应的网页内容....")

        all_results = []
        coze_links = links
        self.logger.info(f"共 {len(links)} 个链接，coze处理 {len(coze_links)} 个")

        batch_size = self.fetch_url_batch

        async def fetch_coze():
            results = []
            for i in range(0, len(coze_links), batch_size):
                batch = coze_links[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(coze_links) + batch_size - 1) // batch_size
                self.logger.info(
                    f"Coze 批次 {batch_num}/{total_batches}: 处理 {len(batch)} 个链接 (进度: {min(i + batch_size, len(coze_links))}/{len(coze_links)})"
                )
                tasks = [asyncio.to_thread(coze_fetch, url) for url in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend(batch_results)
            return results

        coze_results = await asyncio.gather(fetch_coze())

        for i, url in enumerate(coze_links):
            result = coze_results[0][i]
            if (
                not isinstance(result, Exception)
                and result
                and "null" not in str(result)
            ):
                all_results.append({"url": url, "content": result})
            else:
                self.logger.error(f"coze 获取链接内容失败 {url}，错误信息: {result}")

        end_time = time.time()
        self.logger.info(
            f"获取所有链接耗时: {end_time - time_start} 秒，共获取 {len(all_results)} 条内容"
        )
        return all_results

    async def compress_content(self, all_content):
        """压缩网页内容"""
        time_start = time.time()
        self.logger.info("压缩网页内容....")

        # 计算日期范围（过去24小时）
        now = datetime.now()
        start_time = now - timedelta(hours=24)
        date_range = f"{start_time.strftime('%Y/%m/%d %H:%M')} - {now.strftime('%Y/%m/%d %H:%M')}"
        self.logger.info(f"压缩内容日期范围: {date_range}")

        all_results = []
        batch_size = self.compress_num

        for i in range(0, len(all_content), batch_size):
            batch = all_content[i : i + batch_size]
            total_batches = (len(all_content) + batch_size - 1) // batch_size
            current_batch = i // batch_size + 1
            processed = i + len(batch)
            self.logger.info(
                f"压缩批次 {current_batch}/{total_batches}: {len(batch)} 个网页 (进度: {processed}/{len(all_content)})"
            )

            text = ""
            for idx, item in enumerate(batch, start=1):
                content = item.get("content", "")
                text += f"网页{idx}：\n{content}\n"
                text += "====================\n"

            prompt = compress_content_prompt.format(
                text=text, date_range=date_range
            ).strip()
            self.logger.info(f"压缩网页内容 prompt 长度: {len(prompt)} 字符")
            response = call_llm_with_retry(self.llm, prompt, self.logger)
            self.logger.info(f"大模型压缩结果：\n{str(response.content)}")

            compressed_text = str(response.content).strip()
            all_results.append(compressed_text)

        end_time = time.time()
        self.logger.info(
            f"压缩网页内容耗时: {end_time - time_start} 秒，共压缩得到 {len(all_results)} 个压缩内容"
        )
        return all_results

    async def summary_today(self, compressed_results, reference_summaries):
        """总结今天的结果"""
        time_start = time.time()
        self.logger.info("总结今天的结果....")

        try:
            text = reference_summaries + "====================\n"
            for idx, compressed_content in enumerate(compressed_results, start=1):
                text += f"{compressed_content}\n"
                text += "====================\n"

            prompt = summary_today_prompt.format(text=text).strip()
            self.logger.info(f"总结今天的结果 prompt 长度: {len(prompt)} 字符")
            response = call_llm_with_retry(self.llm, prompt, self.logger)
            self.logger.info(f"大模型总结结果：\n{response.content}")

            end_time = time.time()
            self.logger.info(f"总结今天的结果耗时: {end_time - time_start} 秒")

            return response.content

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"总结今天的结果失败: {str(e)}")
            return ""

    async def save_to_db(self, content):
        """保存到数据库，sql"""
        self.logger.info("保存到数据库....")

        try:
            # 创建 db 文件夹
            db_dir = Path("db")
            db_dir.mkdir(exist_ok=True)
            self.logger.info(f"数据库目录: {db_dir.absolute()}")

            # 数据库路径
            db_path = db_dir / "ai_today_news.db"
            self.logger.info(f"数据库路径: {db_path.absolute()}")

            # 连接数据库
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 创建表（如果不存在）
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS today_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """
            )
            self.logger.info("表 today_news 已确保存在")

            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 插入数据
            cursor.execute(
                "INSERT INTO today_news (created_at, content) VALUES (?, ?)",
                (current_time, content),
            )

            # 提交事务
            conn.commit()
            self.logger.info(f"成功保存数据到数据库，时间: {current_time}")

            # 关闭连接
            conn.close()

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"保存到数据库失败: {str(e)}")

    async def read_last_week_news(self):
        """读取过去一周新闻"""
        self.logger.info("读取过去一周新闻....")

        try:
            # 数据库路径
            db_path = Path("db") / "ai_today_news.db"

            # 检查数据库是否存在
            if not db_path.exists():
                self.logger.warning(f"数据库文件不存在: {db_path.absolute()}")
                return []

            # 连接数据库
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 计算过去7天的日期范围
            today = datetime.now()
            one_week_ago = today - timedelta(days=6)
            start_date = one_week_ago.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            self.logger.info(f"查询日期范围: {start_date} 至 {end_date}（共7天）")

            # 查询过去7天的新闻（使用date函数比较日期部分）
            sql = "SELECT id, created_at, content FROM today_news WHERE date(created_at) >= date(?) AND date(created_at) <= date(?) ORDER BY created_at"
            self.logger.info(
                f"完整SQL: {sql} 参数: start_date={start_date}, end_date={end_date}"
            )

            cursor.execute(sql, (start_date, end_date))

            # 获取查询结果
            results = cursor.fetchall()
            self.logger.info(f"查询到 {len(results)} 天过去一周(6天)的新闻")

            # 格式化结果
            news_list = []
            for row in results:
                news_list.append(
                    {"id": row[0], "created_at": row[1], "content": row[2]}
                )

            # 关闭连接
            conn.close()

            # 拼接内容
            if news_list:
                content_list = []
                for news in news_list:
                    content_list.append(
                        f"日期：{news['created_at']}\n{news['content']}\n======="
                    )
                combined_content = "\n".join(content_list)
                self.logger.info(f"拼接完成，共 {len(news_list)} 天新闻")
                self.logger.info(f"部分内容：{combined_content}")
                return combined_content
            else:
                self.logger.info("没有查询到新闻，返回空字符串")
                return ""

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"读取过去一周新闻失败: {str(e)}")
            return []

    async def analyze_last_week_news(self, today_results, last_week_news):
        """分析过去一周新闻"""
        self.logger.info("分析过去一周新闻....")

        try:
            # 构造提示词
            prompt = analyze_last_week_prompt.format(
                last_week_news=last_week_news,
            ).strip()
            self.logger.info(f"分析过去一周新闻 prompt 长度: {len(prompt)} 字符")

            # 调用大模型进行分析
            response = call_llm_with_retry(self.llm, prompt, self.logger)
            self.logger.info(f"大模型分析结果：\n{response.content}")

            # 拼接结果：today_results + 分析结果
            final_result = f"{today_results}\n\n{response.content}"

            return final_result

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"分析过去一周新闻失败: {str(e)}")
            return today_results
