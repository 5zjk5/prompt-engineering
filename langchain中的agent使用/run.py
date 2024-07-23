# coding:utf8
from tools.test_tool import test_tools
from llm.llm_glm import zhipu_glm_4
from llm.llm_tongyi import tongyi_qwen_turbo
from agent.agent import (
    self_ask_with_search, react_agent, react_chat_agent, agent_structured_chat, json_agent, xml_agent,
    agent_plane_execute, agent_openai_tools
)


glm4 = zhipu_glm_4(temperature=0.1)
qwen_turbo = tongyi_qwen_turbo(temperature=0.1)

agent_type = 'agent_openai_tools'
debug = True


if __name__ == '__main__':
    query = '给我介绍下langchain是什么。顺便介绍下美短这个品种的猫'
    if agent_type == 'self_ask_with_search_agent':
        agent = self_ask_with_search(qwen_turbo, test_tools, verbose=debug)
        res = agent.invoke({"input": query})
    if agent_type == 'react_agent':
        agent = react_agent(glm4, test_tools, verbose=debug)
        res = agent.invoke({"input": query})
        res = agent.invoke({"input": res})
    if agent_type == 'react_chat_agent':
        agent = react_chat_agent(glm4, test_tools, verbose=debug)
        res = agent.invoke({"input": query + '中文回答', "chat_history": ''})
        res = agent.invoke({"input": res, "chat_history": ''})
    if agent_type == 'agent_structured_chat':
        agent = agent_structured_chat(glm4, test_tools, verbose=debug)
        res = agent.invoke({"input": query, "chat_history": []})
    if agent_type == 'json_agent':
        agent = agent_structured_chat(glm4, test_tools, verbose=debug)
        res = agent.invoke({"input": query, "chat_history": []})
    if agent_type == 'xml_agent':
        agent = agent_structured_chat(glm4, test_tools, verbose=debug)
        res = agent.invoke({"input": query, "chat_history": []})
    if agent_type == 'agent_plane_execute':
        agent = agent_plane_execute(glm4, test_tools, verbose=debug)
        res = agent.run(query + '中文回答')
    if agent_type == 'agent_openai_tools':
        agent = agent_openai_tools(glm4, test_tools, verbose=debug)
        res = agent.invoke({"messages": [("human", query)], "chat_history": []})
    print(res)
