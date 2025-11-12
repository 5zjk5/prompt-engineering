import traceback
from api.llm_api import llm
from deepsearch.prompt.prompt_lang import formulate_query_prompt
from deepsearch.prompt.prompt_lang import summary_crawl_prompt
from deepsearch.prompt.prompt_lang import final_summary_prompt
from deepsearch.utils.parse_data import parse_query_list


async def formulate_query(topic, have_query, summary_search, logger, query_num=5):
    """
    根据 topic 规划出 num 个 query

    Args:
        topic: 深度搜索主题
        have_query: 已有 query
        logger: 日志
        query_num: query 生成数量
        summary_search: 已有的搜索总结

    Returns:
        queries 列表
    """
    try:
        logger.info(f"开始根据 topic 规划 query！")

        prompt = formulate_query_prompt.format(topic=topic, query_num=query_num, have_query=have_query, summary_search=summary_search).strip()
        logger.info(f"规划 query prompt：\n{prompt}")

        logger.info(f"调用 LLM 规划 query...")
        response = await llm.infer(prompt)
        logger.info(f"规划 query 结果：\n{response}")

        logger.info(f'解析 query 规划结果...')
        query_list = parse_query_list(response)
        logger.info(f'解析 query 规划结果 query 列表：\n{query_list}')

        return query_list

    except Exception as e:
        logger.error(f'topic 规划 query 失败！')
        logger.error(traceback.print_exc())
        return []


async def summarize_crawl_res(crawl_res, topic, summary_search, logger):
    """
    根据爬取结果，进行总结，斌判断是否满足了 topic 要求

    Args:
        crawl_res: 爬取网页结果
        topic: 深度搜索主题
        summary_search: 前面轮次的总结结果
        logger: 日志

    Returns:
        总结结果及判断结果
    """
    try:
        logger.info(f"开始评估，总结新内容...")

        prompt = summary_crawl_prompt.format(topic=topic, summary_search=summary_search, crawl_res=crawl_res).strip()
        logger.info(f"评估，总结新内容 prompt：\n{prompt}")

        logger.info(f"调用 LLM 评估，总结新内容...")
        response = await llm.infer(prompt, enable_thinking=False)  # 评估反思单独加深度思考
        logger.info(f"评估，总结新内容结果：\n{response}")

        response = response.lower() if response else ''
        answer = response.split('总结')[0]
        answer = answer.split('分析')[0]
        summary = response.split('总结')
        if len(summary) > 2:
            summary = ''.join(summary[1:])
        else:
            summary = summary[-1]
        summary = summary.replace('\n', '')
        logger.info(f'解析后评估，总结新内容：\n评估：{answer}\n总结：{summary}')

        return answer, summary

    except Exception as e:
        logger.error(f'评估，总结新内容失败！')
        logger.error(traceback.format_exc())
        return 'no', ''


async def final_summary(topic, summary_search, logger):
    """
    把所有轮次总结的搜索结果汇总做最后的总结

    Args:
        summary_search: list 所有搜索结果的总结，一个元素代表一轮搜索结果的主题
        topic: 深度搜索主题
        logger: 日志

    Returns:
        总结结果
    """
    try:
        logger.info(f"开始最后总结内容...")

        prompt = final_summary_prompt.format(topic=topic, summary_search=summary_search).strip()
        logger.info(f"最后总结内容 prompt：\n{prompt}")

        logger.info(f"调用 LLM 最后总结内容...")
        response = await llm.infer(prompt, temperature=0.2)
        logger.info(f"最后总结内容结果共 {len(response) if response else 0} 字符：\n{response}")

        return response
    except Exception as e:
        logger.error(f'最后总结内容失败！使用每一轮的搜索总结作为结果！')
        logger.error(traceback.format_exc())
        return '。'.join(summary_search)
