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
        "math": {
            "transport": "stdio",  # Local subprocess communication
            "command": "python",
            # Absolute path to your math_server.py file
            "args": [r"C:\Users\admin\Desktop\test\math_service.py"],
        },
    }
)


async def main():
    tools = await client.get_tools()
    agent = create_agent(
        model=model,
        tools=tools  
    )
    math_response = await agent.ainvoke({
        "messages": [{"role": "user", "content": "计算 2 + 3"}]
       }
    )
    print(math_response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
