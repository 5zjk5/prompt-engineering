import asyncio
from agent.agent import create_agent_graph
from agent.state import AgentInputState
from config.config import llm_text
from langchain_core.messages import HumanMessage
from agent.configuration import Configuration


async def main():
    """主函数，用于单独运行agent"""
    agent_graph = await create_agent_graph()

    # 测试运行
    input_state = AgentInputState(messages=[HumanMessage(content="你好")])
    result = await agent_graph.ainvoke(input_state, context=Configuration(llm=llm_text))
    print("非流式测试结果:\n", result['messages'][-1].content)

    print('流式测试结果:')
    async for chunk in agent_graph.astream(
        {"messages": [{"role": "user", "content": "介绍下你自己"}]}, 
        stream_mode="values", context=Configuration(llm=llm_text)):
        latest_message = chunk["messages"][-1]
        if latest_message.content:
            print(latest_message.content, end='')
        elif latest_message.tool_calls:
            print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")


if __name__ == "__main__":
    asyncio.run(main())
