# coding:utf8
from langchain.agents import initialize_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    ChatMessagePromptTemplate,
    PromptTemplate,
)
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain.agents import (
    AgentExecutor,
    create_self_ask_with_search_agent,
    create_react_agent,
    create_structured_chat_agent,
    create_json_chat_agent,
    create_xml_agent,
    create_openai_tools_agent,
    create_tool_calling_agent,
)
from utils.prompts import (
    self_ask_with_search_prompt,
    react_chat_prompt,
    react_prompt,
    structured_chat_prompt,
    react_json_prompt,
    xml_prompt,
    agent_plane_execute_prompt,
    openai_tools_prompt,
    openai_tools_custom_prompt,
)


def agent_initialize_agent(llm, tools, prompt, verbose=False):
    """
    还有一种隐式调用，initialize_agent，这种会逐渐废弃，就不写了，可以网上找到的
    """



def agent_openai_tools(llm, tools, system_prompt=openai_tools_custom_prompt, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/openai_tools/
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/tool_calling/
    以下这种运行写法是调用非 opanai 模型才能运行的，如果使用 opanai 参考官网运行方式
    可以正常使用多个工具，对于本地加载的模型用不了
    run:
        agent.invoke({"messages": [("human", question)]})
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="chat_history")
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=4,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def agent_plane_execute(llm, tools, prompt=agent_plane_execute_prompt, verbose=False):
    """
        run：
         agent.run(question + '中文回答')
    这是一个试验的 agent 规划有时候怪怪的，感觉不是很靠谱，但能调用多个工具
    """
    planner = load_chat_planner(llm, system_prompt=prompt)
    executor = load_agent_executor(llm, tools, verbose=verbose)
    # 初始化Plan-and-Execute Agent
    agent = PlanAndExecute(planner=planner, executor=executor, verbose=verbose)
    return agent


def xml_agent(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/xml_agent/
    Some language models (like Anthropic's Claude) are particularly good at reasoning/writing XML.
    This goes over how to use an agent that uses XML when prompting.
    agent.invoke({"input": query, "chat_history": []})
    这个能正常调用两个工具，chat_history 可以带记忆
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=("You are a helpful assistant!")),
            HumanMessagePromptTemplate.from_template(xml_prompt),
        ]
    )
    agent = create_xml_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=4,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def json_agent(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/json_agent/
    agent.invoke({"input": query, "chat_history": []})
    Some language models are particularly good at writing JSON. This agent uses JSON to format its outputs,
    and is aimed at supporting Chat Models.
    agent.invoke({"input": query, "chat_history": []})
    这个能正常调用两个工具，chat_history 可以带记忆
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=("You are a helpful assistant!")),
            HumanMessagePromptTemplate.from_template(react_json_prompt),
        ]
    )
    agent = create_json_chat_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=4,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def agent_structured_chat(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/structured_chat/
    run：
    agent.invoke({"input": query, "chat_history": []})
    这个能正常调用两个工具，chat_history 可以带记忆
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=("You are a helpful assistant!")),
            HumanMessagePromptTemplate.from_template(structured_chat_prompt),
        ]
    )
    agent = create_structured_chat_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=4,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def react_chat_agent(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/react/
    agent_executor.invoke({"input": query, "chat_history": xxxx})
    带有记忆的 agent
    智谱，通义都可以用，
    但多个工具，都只调用一个就结束了，有点问题
    """
    prompt = PromptTemplate.from_template(react_chat_prompt)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=1,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def react_agent(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/react/
    agent_executor.invoke({"input": "query})
    智谱，通义都可以用，
    但多个工具，都只调用一个就结束了，有点问题，可以调用两次 agent，但就达不到自动规划效果了
    """
    prompt = PromptTemplate.from_template(react_prompt)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=1,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def self_ask_with_search(llm, tools, verbose=False):
    """
    https://python.langchain.com/v0.1/docs/modules/agents/agent_types/self_ask_with_search/
    agent_executor.invoke({"input": "query})
    此 agent
    智谱不支持此 agent，会报错
    通义支持
    """
    prompt = PromptTemplate.from_template(self_ask_with_search_prompt)
    agent = create_self_ask_with_search_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,  # 是否打印过程
        handle_parsing_errors=True,  # 是否处理解析错误，如果解析不了，会重新尝试，但可能会一直重复死循环
        max_iterations=1,  # 如果重新尝试，最大尝试次数，防止无限死循环下去
        return_intermediate_steps=True,  # 如果死循环了，可以加这个参数，返回中间过程步骤，中间步骤可以当结果
        # early_stopping_method="generate",  # 这个参数没有实现有问题：https://github.com/langchain-ai/langchain/issues/16263
        max_execution_time=60,  # 如果死循环了，可以加这个参数，强制停止,通过时间来进行循环的限制
    )
    return agent_executor


def _handle_error(error) -> str:
    return str(error)[:50]
