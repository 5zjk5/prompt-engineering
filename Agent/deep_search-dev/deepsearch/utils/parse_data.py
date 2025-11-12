import os
import re
import json
from datetime import datetime
from fastapi import HTTPException


def parse_query_list(query_list):
    """
    大模型生成的列表 query 解析为 list，斌验证搜索时间是否符合要求，不符合要求赋值为 common

    Args:
        query_list: llm 拆解的 query

    Returns:
        列表
    """
    query_list = re_parse_list(query_list)
    if query_list:
        if isinstance(query_list, str):
            query_list = eval(query_list)
    else:
        query_list = []
    return query_list


def re_parse_list(string):
    """
    正则提取大模型输出的列表字符串

    Args:
        string: markdown 格式字符串列表

    Returns:
        列表
    """
    lst = re.findall(r'```python(.*?)```', string, re.S)
    if len(lst) > 0:
        return eval(lst[0])
    else:
        return []


def save_deepsearch_data(topic, have_query, summary_search, summary_text, epoch, project_root, crawl_res_lst, logger, mode):
    """
    保存中间数据及所有结果

    Args:
        topic: str 主题
        have_query: list 拆解所有 query
        summary_search: list 所有轮次搜索结果总结的结果
        summary_text: str 最后总结输出的 markdown
        epoch: int 深度搜索轮次
        project_root: str 项目根目录
        crawl_res_lst: lst 搜索爬虫原始结果
        logger: 日志
        mode: 模式

    Returns:
        none
    """
    try:
        data = {
            'topic': topic,
            'have_query': have_query,
            'summary_search': summary_search,
            'summary_text': summary_text,
            'crawl_res': crawl_res_lst,
            'epoch': epoch,
            'mode': mode
        }

        now = datetime.now()
        date_time = now.strftime("%Y%m%d_%H%M%S")

        save_dir = os.path.join(project_root, 'eval', 'deepsearch_data')
        os.makedirs(save_dir, exist_ok=True)
        topic = re.sub(r'[\/\\:\*\?"<>\|]', '_', topic)
        save_path = os.path.join(save_dir, f"{topic[:30]}_{date_time}.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logger.info(f'保存中间数据及所有结果成功！')
    except Exception as e:
        logger.error(f"保存中间数据及所有结果失败：{e}")


def save_deepresearch_data(topic, summary_text, subtask_res, project_root, logger, mode):
    """
    保存中间数据及所有结果

    Args:
        topic: str 主题
        summary_text: str 最后总结输出的 markdown
        subtask_res: str 拆解子任务执行结果
        project_root: str 项目根目录
        logger: 日志
        mode: 模式

    Returns:
        none
    """
    try:
        data = {
            'topic': topic,
            'subtask_res': subtask_res,
            'summary_text': summary_text,
            'mode': mode
        }

        now = datetime.now()
        date_time = now.strftime("%Y%m%d_%H%M%S")

        save_dir = os.path.join(project_root, 'eval', 'deepResearch_data')
        os.makedirs(save_dir, exist_ok=True)
        topic = re.sub(r'[\/\\:\*\?"<>\|]', '_', topic)
        save_path = os.path.join(save_dir, f"{topic[:30]}_{date_time}.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logger.info(f'保存中间数据及所有结果成功！')
    except Exception as e:
        logger.error(f"保存中间数据及所有结果失败：{e}")


def verify_params(topic):
    """
    深度搜索入参校验

    Args:
        topic: str 主题

    Returns:
        none
    """
    topic = topic.strip().replace('/', ',').replace('\\', ',')
    if not topic:
        raise HTTPException(status_code=500, detail="主题 topic 不能为空")
    return topic
