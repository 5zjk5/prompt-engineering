import requests
import os
import json
import traceback
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from ddgs import DDGS
from cozepy import COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType


def duckduckgo_search(query, region="cn-zh", max_results=20, timelimit="d"):
    """
    使用 DuckDuckGo 搜索引擎进行搜索

    参数:
        query (str): 搜索查询关键词
        region (str): 用于搜索的区域，例如 'wt-wt' (全球) 或 'cn-zh' (中国)
        max_results (int): 返回的最大结果数量，默认为 10
        timelimit (str): 搜索的时间限制，例如 'd' (天)、'w' (周)、'm' (月)、'y' (年)

    返回:
        list: 搜索结果列表，每个元素包含 title、url、summary 等字段
    """
    encoded_query = quote(query, safe="")
    with DDGS() as ddgs:
        results = ddgs.text(
            encoded_query, region=region, max_results=max_results, timelimit=timelimit
        )
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "summary": result.get("body", ""),
                }
            )
        return formatted_results


def huoshan_search(query, count=20):
    """
    火山搜索

    Args:
        query (str): 用户输入的关键词
    Returns:
        list: 搜索结果列表
    """
    COZE_API_TOKEN = os.getenv("COZE_API_TOKEN")
    COZE_API_URL = os.getenv("COZE_API_URL")
    WORKFLOW_ID = os.getenv("SEARCH_WORKFLOW_ID")
    coze = Coze(auth=TokenAuth(token=COZE_API_TOKEN), base_url=COZE_CN_BASE_URL)
    workflow = coze.workflows.runs.create(
        workflow_id=WORKFLOW_ID,
        parameters={"USER_INPUT": query, "count": count},
    )
    results = json.loads(workflow.data)
    data_list = results.get("output").get("doc_results")

    # 解析
    formatted_results = []
    if not data_list:
        return []
    for output_item in data_list:
        sitename = output_item.get("sitename", "")
        summary = output_item.get("summary", "")
        title = output_item.get("title", "")
        url = output_item.get("url", "")

        result_dict = {
            "sitename": sitename,
            "summary": summary,
            "title": title,
            "url": url,
        }

        formatted_results.append(result_dict)

    return formatted_results


if __name__ == "__main__":
    from pathlib import Path

    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    querys = ['(2026/04/11 21:14 - 2026/04/12 21:14) (AI news OR highlights) site:kite.kagi.com OR site:tldr.tech OR site:venturebeat.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 新闻 OR 要闻) site:news.aibase.com OR site:jiqizhixin.com OR site:qbitai.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (release OR update OR launch) site:openai.com OR site:anthropic.com OR site:blog.google OR site:microsoft.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (GLM-5 OR DeepSeek OR Qwen OR 豆包) (发布 OR 更新) site:zhipuai.cn OR site:deepseek.com OR site:qwenlm.github.io OR site:volcengine.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI agent OR agentic security OR framework) site:venturebeat.com OR site:arstechnica.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (Cursor OR Claude Code OR LangChain OR Ollama) (update OR changelog OR feature)', '(2026/04/11 21:14 - 2026/04/12 21:14) (trending OR stars) (AI OR LLM) site:github.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (开源 OR 项目) (AI OR LLM) site:v2ex.com OR site:juejin.cn', '(2026/04/11 21:14 - 2026/04/12 21:14) (release notes) repo:langchain-ai/langchain OR repo:ollama/ollama OR repo:cursorsh/cursor', '(2026/04/11 21:14 - 2026/04/12 21:14) (LLM paper OR SOTA) site:arxiv.org OR site:huggingface.co/papers', '(2026/04/11 21:14 - 2026/04/12 21:14) (GPT OR Claude) (update OR release OR feature) site:openai.com OR site:anthropic.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (LLaMA OR Mistral) (release OR update OR model) site:meta.com OR site:mistral.ai', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI agent OR framework) (release OR update) site:langchain.com OR site:crewai.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (code generation OR AI coding) (update OR feature) site:cursor.sh OR site:replit.com OR site:v0.dev', 'OR site:bolt.new', '(2026/04/11 21:14 - 2026/04/12 21:14) (SKILL OR multimodal OR on-device AI) (application OR deployment)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI Agent OR embodied AI OR AI + X) (trend OR news) site:technologyreview.com OR site:wired.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (Hugging Face OR GitHub) (trending OR model release) site:huggingface.co OR site:github.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (Google OR Microsoft OR Meta) (AI product OR launch) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 工具 OR 辅助开发) (更新 OR 发布) site:ifanr.com OR site:36kr.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (大模型 OR LLM) (应用场景 OR 落地) site:csdn.net OR site:zhihu.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 芯片 OR 算力) (发布 OR 进展) site:semianalysis.com OR site:tomshardware.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI safety OR alignment) (research OR paper) site:openai.com OR site:anthropic.com OR site:deepmind.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (Transformer OR diffusion) (architecture OR improvement) (AI OR LLM)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 创业 OR 融资) (2026/04/11..2026/04/12) site:techcrunch.com OR site:theinformation.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (OpenAI Assistants OR Anthropic Tool Use) (update OR guide)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AutoGPT OR BabyAGI) (update OR release) site:github.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (RAG OR vector database) (optimization OR framework) site:pinecone.io OR site:weaviate.io', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 视觉 OR 多模态) (模型 OR 应用) site:arxiv.org OR site:huggingface.co', '(2026/04/11 21:14 - 2026/04/12 21:14) (LangGraph OR LlamaIndex) (release OR feature) site:langchain.com OR site:llamaindex.ai', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 监管 OR 政策) (2026/04/11..2026/04/12) site:europa.eu OR site:whitehouse.gov', '(2026/04/11 21:14 - 2026/04/12 21:14) (端侧 AI OR 手机 AI) (发布 OR 应用) site:qualcomm.com OR site:apple.com OR site:samsung.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 编程助手 OR Copilot) (更新 OR 竞品) site:github.com OR site:jetbrains.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (推理加速 OR 模型量化) (tool OR framework) site:vllm.ai OR site:tensorrt.llm', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 数据集 OR 训练数据) (release OR benchmark) site:huggingface.co', '(2026/04/11 21:14 - 2026/04/12 21:14) (GPT-5 OR Claude 4) (rumor OR leak OR announcement)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 搜索引擎 OR Perplexity) (update OR feature) site:perplexity.ai', '(2026/04/11 21:14 - 2026/04/12 21:14) (具身智能 OR 机器人) (AI 模型 OR 应用) site:tesla.com OR site:bostondynamics.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 音乐 OR 视频) (生成 OR 模型) site:suno.com OR site:runway.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (WebGPU OR WebNN) (AI OR LLM) (browser OR framework)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 芯片推理 OR 边缘计算) (2026/04/11..2026/04/12) site:nvidia.com OR site:amd.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (Prompt engineering OR instruction tuning) (guide OR paper) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 评测 OR 基准测试) (LLM OR 模型) (2026/04/11..2026/04/12) site:lmsys.org', '(2026/04/11 21:14 - 2026/04/12 21:14) (DeepSeek R1 OR Qwen 2.5) (发布 OR 能力评测)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI Agent 工作流 OR 编排) (tool OR platform) site:dust.tt OR site:langflow.org', '(2026/04/11 21:14 - 2026/04/12 21:14) (开源大模型 OR Open LLM) (榜单 OR 排行) site:huggingface.co', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI API OR pricing) (update OR change) site:openai.com OR site:anthropic.com OR site:deepseek.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (长上下文 OR Long Context) (突破 OR 应用) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 辅助教育 OR AI Tutor) (产品 OR 应用) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 安全漏洞 OR prompt injection) (漏洞 OR 防护) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 设计 OR UI 生成) (工具 OR 更新) site:v0.dev OR site:uizard.io', '(2026/04/11 21:14 - 2026/04/12 21:14) (多模态 Agent OR Vision Agent) (研究 OR 应用) (2026/04/11..2026/04/12)', '(2026/04/11 21:14 - 2026/04/12 21:14) (模型微调 OR LoRA) (工具 OR 平台) (2026/04/11..2026/04/12) site:modal.com OR site:replicate.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI news OR highlights) site:kite.kagi.com OR site:tldr.tech OR site:venturebeat.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI 新闻 OR 要闻) site:news.aibase.com OR site:jiqizhixin.com OR site:qbitai.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (release OR update OR launch) site:openai.com OR site:anthropic.com OR site:blog.google OR site:microsoft.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (GLM-5 OR DeepSeek OR Qwen OR 豆包) (发布 OR 更新) site:zhipuai.cn OR site:deepseek.com OR site:qwenlm.github.io OR site:volcengine.com', '(2026/04/11 21:14 - 2026/04/12 21:14) (AI agent OR agentic security OR framework) site:venturebeat.com OR site:arstechnica.com',]

    print("=" * 50)
    print("测试并发:")
    test_queries = querys[:]
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {
            executor.submit(duckduckgo_search, q, 'cn-zh', 20, 'd'): q
            for q in test_queries
        }
        # future_to_query = {
        #     executor.submit(huoshan_search, q, count=20): q for q in test_queries
        # }
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results = future.result()
                print(f"查询: {query} -> 共找到 {len(results)} 条结果")
            except Exception as e:
                print(f"查询: {query} -> 错误: {e}")
                traceback.print_exc()
            pass

    # print("测试 DuckDuckGo 搜索:")
    # results = duckduckgo_search(
    #     "'(2026/04/11 10:34 - 2026/04/12 10:34) (LangChain OR CrewAI OR AutoGPT OR OpenAI Assistants OR Anthropic Tool Use) (update OR release OR new feature) site:langchain.com OR site:crewai.io OR site:autogpt.org OR site:openai.com/assistants OR site:anthropic.com/tool-use'",
    #     region='cn-zh', max_results=20, timelimit='d'
    # )
    # print(f"共找到 {len(results)} 条结果")
    # print(results[0])

    # print("=" * 50)
    # print("测试火山搜索接口:")
    # search_result = huoshan_search("技术热点", count=20)
    # print(f"返回结果数: {len(search_result)}")
    # print(search_result[0])
