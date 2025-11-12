# coding:utf8
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain import hub
from langchain.agents import initialize_agent
from langchain.prompts import PromptTemplate


def create_agent_openai_tools(llm: ChatOpenAI, tools: list, system_prompt, debug: bool = False):
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


def create_agent_plane_execute(llm: ChatOpenAI, tools: list, system_prompt, debug: bool = False):
    """
        run：
         agent.run(question + '中文回答')
    """
    planner = load_chat_planner(llm, system_prompt=system_prompt)
    executor = load_agent_executor(llm, tools, verbose=debug)
    # 初始化Plan-and-Execute Agent
    agent = PlanAndExecute(planner=planner, executor=executor, verbose=debug)
    return agent


def create_agent_structured_chat(llm: ChatOpenAI, tools: list, system_prompt, debug: bool = False):
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


def create_initialize_agent(llm, tools, verbose=False):
    """
    agent.invoke({"input": '最后用中文回答' + generate_sql})
    """
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type="zero_shot",
        prompt_template=PromptTemplate(
            template="You are an SQL agent. Execute the following SQL query: {query}",
            input_variables=["query"]
        ),
        verbose=verbose
    )
    return agent
