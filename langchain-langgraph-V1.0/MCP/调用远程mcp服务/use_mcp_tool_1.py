# https://docs.langchain.com/oss/python/langchain/mcp#use-mcp-tools

from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


model = ChatOpenAI(
    temperature=0.7,
    model="glm-4-flash",
    openai_api_key="",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)

client = MultiServerMCPClient(  
    {
        "Weather": {  # Weather 为服务名，大小写不影响
            "transport": "streamable_http",  # HTTP-based remote server
            # Ensure you start your weather server on port 8000
            "url": "http://localhost:8000/mcp",
        }
    }
)


async def main():
    tools = await client.get_tools()
    agent = create_agent(
        model=model,
        tools=tools  
    )
    math_response = await agent.ainvoke({
        "messages": [{"role": "user", "content": "纽约的天氣如何？"}]
       }
    )
    print(math_response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
