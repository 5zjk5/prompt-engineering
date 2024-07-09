# coding:utf8
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain import hub


template_prompt = """
你是一个法律行业的智能助手，擅长对用户问题进行拆解多个步骤，并一步一步推理，可以调用合适的工具，最后将推理结果组合成答案。
"""

agent_prompt = """
你是一个法律行业的智能助手，擅长对用户问题进行拆解多个步骤，并一步一步推理，并且根据逻辑顺序一步一步调用工具，最后将推理结果组合成答案。
**工具调用顺序至关重要**，例如问题"(2019)内民终564号案件的被告律师事务所地址在什么地方"需要先根据案号查询到律师事务所，再去查询律师事务所地址，
不能直接先查询到律师事务所或地址，一定要先查询案号。
**提取出问题中的关键信息非常重要**，例如问题"审理(2019)川0129民初1361号案件的法院名称是哪个法院，地址在什么地方"，要回答这个问题，
需要先提取出案号'(2019)川0129民初1361号'去调用案号相关的工具。
**工具的选择至关重要**，例如问题"统一社会信用代码是913310007200456372这家公司的法人是谁"必选先使用'根据统一社会信用代码查询公司名称'相关工具获得
公司名称，再使用'根据公司名称查询工商信息'的工具获得法人。
"""


def create_agent_openai_tools(llm: ChatOpenAI, tools: list, system_prompt: str = template_prompt, debug: bool = False):
    """
    run:
        agent.invoke({"messages": [("human", question)]})
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=debug)
    return executor


def create_agent_plane_execute(llm: ChatOpenAI, tools: list, system_prompt: str = template_prompt, debug: bool = False):
    """
        run：
         agent.run(question + '中文回答')
    """
    planner = load_chat_planner(llm, system_prompt=system_prompt)
    executor = load_agent_executor(llm, tools, verbose=debug)
    # 初始化Plan-and-Execute Agent
    agent = PlanAndExecute(planner=planner, executor=executor, verbose=debug)
    return agent


def create_agent_structured_chat(llm: ChatOpenAI, tools: list, system_prompt: str = template_prompt, debug: bool = False):
    """
    run：
    agent_executor.invoke({"input": question})
    """
    prompt = hub.pull("hwchase17/structured-chat-agent")
    agent = create_structured_chat_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )
    return agent_executor
