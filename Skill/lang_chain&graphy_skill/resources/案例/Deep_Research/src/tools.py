import asyncio
import logging
import os
from datetime import datetime
from typing import Annotated, List, Literal
from langchain_core.tools import InjectedToolArg, tool
from langchain_core.messages import HumanMessage
from src.configuration import Configuration
from src.llm import configurable_model
from src.state import Summary
from src.prompts import summarize_webpage_prompt
from tavily import AsyncTavilyClient
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig


def get_today_str() -> str:
    """
    获取用于提示和输出的当前日期格式化字符串。

    返回：人类可读的日期字符串，格式类似于'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"


class ConductResearch(BaseModel):
    """调用此工具对特定主题进行研究"""
    research_topic: str = Field(
        description="研究主题。应该是一个单独的主题，并且应该用高细节描述（至少是一个段落）。",
    )


class ResearchComplete(BaseModel):
    """调用此工具表示研究已完成"""


@tool(description="研究规划的战略反思工具")
def think_tool(reflection: str) -> str:
    """
    用于对研究进展和决策进行战略反思的工具。

    每次搜索后使用此工具，系统性地分析结果并规划下一步计划。
    这在研究工作流程中创造了有意暂停，以便做出高质量的决策。

    使用时机：
    - 收到搜索结果后：我发现了哪些关键信息？
    - 决定下一步计划前：我有足够的资料来全面回答吗？
    - 评估研究差距时：我仍然缺少哪些具体信息？
    - 总结研究前：我现在能提供完整答案吗？

    反思应涵盖：
    1. 当前发现分析 - 我收集了哪些具体信息？
    2. 差距评估 - 仍然缺少哪些关键信息？
    3. 质量评价 - 我是否有足够的证据/示例来给出一个良好的答案？
    4. 战略决策 - 我是否应该继续搜索或提供我的答案？

    Args：
        reflection: 您对研究进展、发现、差距和下一步计划的详细反思

    Returns：
        反思已记录用于决策的确认
    """
    return f"反思已记录：{reflection}"


##########################
# Tavily Search Tool Utils
##########################
TAVILY_SEARCH_DESCRIPTION = (
    "A search engine optimized for comprehensive, accurate, and trusted results. "
    "Useful for when you need to answer questions about current events."
)
@tool(description=TAVILY_SEARCH_DESCRIPTION)
async def tavily_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 5,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
    config: RunnableConfig = None
) -> str:
    """
    从Tavily搜索API获取并总结搜索结果。

    参数：
        queries：要执行的搜索查询列表
        max_results：每个查询返回的最大结果数
        topic：搜索结果的主题过滤器（通用、新闻或财务）
        config：用于API密钥和模型设置的运行时配置

    返回：
        包含总结搜索结果的格式化字符串
    """
    # Step 1: 异步执行搜索查询
    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
        config=config
    )
    
    # Step 2: 根据URL去重结果，以避免多次处理相同内容
    unique_results = {}
    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = {**result, "query": response['query']}
    
    # Step 3: 设置总结模型，根据配置初始化
    configurable = Configuration.from_runnable_config(config)
    
    # 保持在模型令牌限制内的字符限制（可配置）
    max_char_to_include = configurable.max_content_length
    
    # Initialize summarization model with retry logic
    summarization_model = configurable_model.with_structured_output(Summary).with_retry(
        stop_after_attempt=configurable.max_structured_output_retries
    )
    
    # Step 4: 创建摘要任务（跳过空内容）
    async def noop():
        """无操作函数，用于没有原始内容的结果。"""
        return None
    
    summarization_tasks = [
        noop() if not result.get("raw_content") 
        else summarize_webpage(
            summarization_model, 
            result['raw_content'][:max_char_to_include]
        )
        for result in unique_results.values()
    ]
    
    # Step 5: 并行执行所有摘要任务
    summaries = await asyncio.gather(*summarization_tasks)
    
    # Step 6: 将结果与摘要结合
    summarized_results = {
        url: {
            'title': result['title'], 
            'content': result['content'] if summary is None else summary
        }
        for url, result, summary in zip(
            unique_results.keys(), 
            unique_results.values(), 
            summaries
        )
    }
    
    # Step 7: 格式化最终输出
    if not summarized_results:
        return "未找到有效的搜索结果。请尝试使用不同的搜索查询或使用不同的搜索API。"
    
    formatted_output = "Search results: \n\n"
    for i, (url, result) in enumerate(summarized_results.items()):
        formatted_output += f"\n\n--- SOURCE {i+1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "\n\n" + "-" * 80 + "\n"
    
    return formatted_output


async def tavily_search_async(
    search_queries, 
    max_results: int = 5, 
    topic: Literal["general", "news", "finance"] = "general", 
    include_raw_content: bool = True, 
    config: RunnableConfig = None
):
    """
    异步执行多个Tavily搜索查询。

    参数：
        search_queries：要执行的搜索查询字符串列表
        max_results：每个查询的最大结果数量
        topic：用于筛选结果的分类主题
        include_raw_content：是否包含完整网页内容
        config：API密钥访问的运行时配置

    返回：
        来自Tavily API的搜索结果字典列表，每个字典包含查询、结果数量和结果列表。
        每个结果字典包含标题、URL、内容（如果包含原始内容）和摘要（如果有）。
    """
    # 使用配置中的 API 密钥初始化 Tavily 客户端
    tavily_client = AsyncTavilyClient(api_key=get_tavily_api_key(config))
    
    # Create search tasks for parallel execution
    search_tasks = [
        tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic
        )
        for query in search_queries
    ]
    
    # Execute all search queries in parallel and return results
    search_results = await asyncio.gather(*search_tasks)
    return search_results


def get_tavily_api_key(config: RunnableConfig):
    """Get Tavily API key from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        return api_keys.get("TAVILY_API_KEY")
    else:
        return os.getenv("TAVILY_API_KEY")


async def summarize_webpage(model: BaseChatModel, webpage_content: str) -> str:
    """
    使用AI模型总结网页内容，并带超时保护。

    参数:
        model: 用于摘要的聊天模型
        webpage_content: 要总结的原始网页内容
        
    返回:
        摘要后的格式化内容，其中包含关键摘录，或者在摘要失败时返回原始内容
    """
    try:
        # Create prompt with current date context
        prompt_content = summarize_webpage_prompt.format(
            webpage_content=webpage_content, 
            date=get_today_str()
        )
        
        # Execute summarization with timeout to prevent hanging
        summary = await asyncio.wait_for(
            model.ainvoke([HumanMessage(content=prompt_content)]),
            timeout=60.0  # 60 second timeout for summarization
        )
        
        # Format the summary with structured sections
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )
        
        return formatted_summary
        
    except asyncio.TimeoutError:
        # Timeout during summarization - return original content
        logging.warning("Summarization timed out after 60 seconds, returning original content")
        return webpage_content
    except Exception as e:
        # Other errors during summarization - log and return original content
        logging.warning(f"Summarization failed with error: {str(e)}, returning original content")
        return webpage_content
