# https://docs.langchain.com/langsmith/server-mcp#usage-overview

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


model = ChatOpenAI(
    temperature=0.7,
    model="glm-4-flash",
    openai_api_key="",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)


server_params = {
    "url": "http://localhost:8000/mcp",
    # "headers": {
    #     "X-Api-Key":"lsv2_pt_your_api_key"
    # }
}

async def main():
    async with streamablehttp_client(**server_params) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Load the remote graph as if it was a tool
            tools = await load_mcp_tools(session)

            # Create and run a react agent with the tools
            agent = create_agent(model=model, tools=tools)

            # Invoke the agent with a message
            agent_response = await agent.ainvoke({"messages": "北京的天氣如何？直接调用工具，不要问我"})
            print(agent_response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
