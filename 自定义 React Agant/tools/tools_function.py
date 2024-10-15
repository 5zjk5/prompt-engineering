from tavily import TavilyClient
from llm.llm_api_key import TAVILY_API_KEY
import time


def tavily_search(query):
    try:
        # Step 1. Instantiating your TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

        # Step 2. Executing a Q&A search query
        answer = tavily_client.qna_search(query=query)

        # Step 3. That's it! Your question has been answered!
        return answer
    except:
        time.sleep(1)
        # Step 1. Instantiating your TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

        # Step 2. Executing a Q&A search query
        answer = tavily_client.qna_search(query=query)

        # Step 3. That's it! Your question has been answered!
        return answer


def height_search(name):
    height_dic = {
        "张三": 180,
        "李四": 175,
        "王五": 170,
        "赵六": 165,
        "钱七": 160,
    }
    return height_dic.get(name)
