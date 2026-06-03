import requests
import json
import os
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from cozepy import COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType


def coze_fetch(url):
    """
    火山获取网页内容

    Args:
        url (str): 用户输入的url
    Returns:
        str: 网页内容
    """
    COZE_API_TOKEN = os.getenv("COZE_API_TOKEN")
    COZE_API_URL = os.getenv("COZE_API_URL")
    WORKFLOW_ID = os.getenv("FETCH_WORKFLOW_ID")
    coze = Coze(auth=TokenAuth(token=COZE_API_TOKEN), base_url=COZE_CN_BASE_URL)
    workflow = coze.workflows.runs.create(
        workflow_id=WORKFLOW_ID,
        parameters={"USER_INPUT": url},
    )
    results = json.loads(workflow.data)
    content = results.get("www").get("content")
    return content


def jina_fetch(url):
    """
    jina 获取网页内容

    Args:
        url (str): 用户输入的url
    Returns:
        str: 网页内容
    """
    JINA_API_TOKEN = os.getenv("JINA_API_TOKEN")
    url = f"https://r.jina.ai/{url}"
    headers = {"Authorization": f"Bearer {JINA_API_TOKEN}"}
    response = requests.get(url, headers=headers)
    # response = requests.get(url)
    content = response.text
    return content


def parallel_test(fetch_func, urls, max_workers=5):
    """
    并行测试获取网页内容

    Args:
        fetch_func: 获取网页内容的函数 (coze_fetch 或 jina_fetch)
        urls: 要获取的 URL 列表
        max_workers: 最大并发数，默认为 5
    """
    start_time = time.time()
    results = []
    success_count = 0
    fail_count = 0

    print(f"开始并行测试，并发数: {max_workers}")
    print(f"URL 数量: {len(urls)}")
    print("-" * 50)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_func, url): url for url in urls}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                content = future.result()
                if '402' in str(content):
                    raise Exception(content)
                results.append((url, content, True))
                success_count += 1
                print(f"✓ 成功: {url}")
            except Exception as e:
                results.append((url, str(e), False))
                fail_count += 1
                print(
                    f"✗ 失败: {url} - 错误: {str(e)}"
                )

    end_time = time.time()
    total_time = end_time - start_time

    print("-" * 50)
    print(f"测试完成!")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")

    return results


if __name__ == "__main__":
    from pathlib import Path

    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # 测试用的 URL 列表
    test_urls = [
        "https://www.cursor.com/changelog",
    #     "https://github.blog/changelog/label/copilot/",
    #     "https://blog.csdn.net/zjkpy_5?spm=1000.2115.3001.5343",
    #     'https://news.aibase.com/zh/daily',
    ]

    # 配置并发数
    CONCURRENCY = 20
    # 并行测试 jina_fetch
    print("\n=== 开始并行测试 fetch ===")
    # parallel_test(jina_fetch, test_urls, max_workers=CONCURRENCY)
    parallel_test(coze_fetch, test_urls, max_workers=CONCURRENCY)

    # print("测试 coze fetch 获取网页内容:")
    # content = coze_fetch("https://blog.csdn.net/zjkpy_5?spm=1000.2115.3001.5343")
    # print(content)

    # print("测试 jina fetch 获取网页内容:")
    # content = jina_fetch("https://blog.csdn.net/zjkpy_5?spm=1000.2115.3001.5343")
    # print(content)

