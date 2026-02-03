import os
from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langgraph.runtime import Runtime
from src.configuration import Configuration
from src.subgraph_supervisor_research import supervisor_subgraph
from src.llm import configurable_model
from src.logger import define_log_level
from src.state import (
    AgentState, 
    AgentInputState,
    ClarifyWithUser,
    ResearchQuestion,
)
from src.utils import (
    get_today_str,
)
from src.prompts import (
    clarify_with_user_instructions,
    final_report_generation_prompt,
    lead_researcher_prompt,
    transform_messages_into_research_topic_prompt,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    get_buffer_string,
)


# 根目录
project_root = os.path.dirname(os.path.abspath(__file__))


async def clarify_with_user(
    state: AgentState,
    config: RunnableConfig,
    runtime: Runtime[Configuration]
) -> Command[Literal["write_research_brief", "__end__"]]:
    """
    分析用户消息，如果研究范围不明确，则询问澄清问题。
    此函数确定用户请求是否需要澄清才继续进行研究。如果禁用澄清或不需要澄清，则直接进行研究。

    Args:
        state: 包含用户消息的当前代理状态
        config: 包含模型设置和偏好的运行时配置
        runtime: 运行时环境，包含上下文信息，如 logger

    Returns:
        要么以澄清问题结束的命令，要么继续进行研究简报的命令
    """
    logger = runtime.context.logger
    logger.info(f'========== 当前节点：clarify_with_user start ==========')

    # Step 1: 检查配置是否启用说明
    configurable = Configuration.from_runnable_config(config)
    if not configurable.allow_clarification:
        # 跳过澄清步骤，直接进行研究
        logger.info("澄清步骤被禁用，直接进行研究......")
        return Command(goto="write_research_brief")
    
    # Step 2: 准备模型用于结构化澄清分析
    messages = state["messages"]
    model_config = {
        "tags": ["langsmith:nostream"]  # 调用的输出不会被流式传输，只会在完成后返回完整结果到 langsmith
    }
    
    # 配置模型使用结构化输出和重试逻辑
    clarification_model = (
        configurable_model
        .with_structured_output(ClarifyWithUser)  # 结构化输出字段
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)  # 大模型重试次数
        .with_config(model_config)
    )
    
    # Step 3: 分析是否需要澄清
    prompt_content = clarify_with_user_instructions.format(
        messages=get_buffer_string(messages), 
        date=get_today_str()
    )
    logger.info(f"澄清分析提示:\n{prompt_content}")
    response = await clarification_model.ainvoke([HumanMessage(content=prompt_content)])
    
    # 这里单独加的，有时候结构化输出为 none 了，就是没有提取成功，再来一次可能就好了，这里最好自己写个解析判断，不要用结构化，因为不知道是解析失败，还是模型生成失败
    while not response:
        logger.warning("澄清分析结果为空，重试一次......")
        response = await clarification_model.ainvoke([HumanMessage(content=prompt_content)])
    logger.info(f"澄清分析结果:\n{response}")
    
    # Step 4: 基于澄清分析的路径
    if response.need_clarification:
        # 以澄清问题的形式结束，向用户提问
        logger.info(f"需要澄清，向用户提问：{response.question}")
        logger.info(f'下一节点：END')
        logger.info(f'========== 当前节点：clarify_with_user end ==========')
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        # 进行带验证消息的研究
        logger.info(f"不需要澄清了，进行带验证的消息的研究：{response.verification}")
        logger.info(f'下一节点：write_research_brief')
        logger.info(f'========== 当前节点：clarify_with_user end ==========')
        return Command(
            goto="write_research_brief", 
            update={"messages": [AIMessage(content=response.verification)]}
        )


async def write_research_brief(
    state: AgentState,
    config: RunnableConfig, 
    runtime: Runtime[Configuration]
) -> Command[Literal["research_supervisor"]]:
    """
    将用户消息转换为结构化的研究摘要并初始化主管。
    此函数分析用户的消息，并生成一个集中的研究摘要，以指导研究主管。它还使用适当的提示和说明设置初始主管上下文。

    参数：
        state：包含用户消息的当前代理状态
        config：包含模型设置的运行时配置
        runtime：运行时环境，包含上下文信息，如 logger

    返回：
        命令，以初始化上下文进入研究主管
    """
    logger = runtime.context.logger
    logger.info(f'========== 当前节点：write_research_brief start ==========')
        
    # Step 1: 设置结构化输出的研究模型
    configurable = Configuration.from_runnable_config(config)
    research_model_config = {
        "tags": ["langsmith:nostream"]  # 调用的输出不会被流式传输，只会在完成后返回完整结果到 langsmith
    }
    
    # Configure model for structured research question generation
    research_model = (
        configurable_model
        .with_structured_output(ResearchQuestion)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 2: 根据用户消息生成结构化研究简介
    prompt_content = transform_messages_into_research_topic_prompt.format(
        messages=get_buffer_string(state.get("messages", [])),
        date=get_today_str()
    )
    logger.info(f"研究计划提示:\n{prompt_content}")
    response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
    
    # 这里单独加的，有时候结构化输出为 none 了，就是没有提取成功，再来一次可能就好了，这里最好自己写个解析判断，不要用结构化，因为不知道是解析失败，还是模型生成失败
    while not response:
        logger.warning("研究计划结果为空，重试一次......")
        response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
    logger.info(f"研究计划结果:\n{response}")
    
    # Step 3: 使用研究简报和指令初始化监督者
    supervisor_system_prompt = lead_researcher_prompt.format(
        date=get_today_str(),
        max_concurrent_research_units=configurable.max_concurrent_research_units,
        max_researcher_iterations=configurable.max_researcher_iterations
    )
    
    logger.info(f'下一节点：research_supervisor')
    logger.info(f'========== 当前节点：write_research_brief end ==========')
    return Command(
        goto="research_supervisor", 
        update={
            "research_brief": response.research_brief,
            "supervisor_messages": {
                "type": "override",
                "value": [
                    SystemMessage(content=supervisor_system_prompt),
                    HumanMessage(content=response.research_brief)
                ]
            }
        }
    )


async def final_report_generation(
    state: AgentState,
    config: RunnableConfig, 
    runtime: Runtime[Configuration]
):
    """
    生成最终的综合研究报告，具有令牌限制的重试逻辑。
    该函数将所有收集到的研究成果整合起来，并使用配置的报告生成模型将其合成一个结构良好、内容全面的最終报告。
    不需要写返回节点定义了，因为没有用 command，直接返回字典了。

    参数：
        state：包含研究成果和上下文的代理状态
        config：包含模型设置和API密钥的运行时配置
        runtime：运行时环境，包含上下文信息，如 logger

    返回值：
        包含最终报告和已清除状态的字典
    """
    logger = runtime.context.logger
    logger.info(f'========== final_report_generation start ==========')

    # Step 1: E提取研究成果，准备状态清理工作
    notes = state.get("notes", [])
    cleared_state = {"notes": {"type": "override", "value": []}}
    findings = "\n".join(notes)
    
    # Step 2: 配置最终报告生成模型
    configurable = Configuration.from_runnable_config(config)
    writer_model_config = {
        "tags": ["langsmith:nostream"]
    }
    
    # Step 3: 尝试使用带token限制的重试逻辑来生成报告
    max_retries = 3
    current_retry = 0
    findings_len = len(findings)  # 这里改了用来字符数截断
    
    while current_retry <= max_retries:
        try:
            # 创建包含所有研究背景的完整提示
            final_report_prompt = final_report_generation_prompt.format(
                research_brief=state.get("research_brief", ""),
                messages=get_buffer_string(state.get("messages", [])),
                findings=findings,
                date=get_today_str()
            )
            logger.info(f"最终报告提示:\n{final_report_prompt}")
            
            # 生成最终报告
            final_report = await configurable_model.with_config(writer_model_config).ainvoke([
                HumanMessage(content=final_report_prompt)
            ])
            logger.info(f"最终报告结果:\n{final_report.content}")
            
            # 如果成功生成报告，返回成功结果
            return {
                "final_report": final_report.content, 
                "messages": [final_report],
                **cleared_state
            }
            
        except Exception as e:
            # 处理令牌超出限制错误，通过逐步截断 findings 来重试
            if 'too lagre' in str(e):  # 这里是模拟错误，根据实际模型报错进行修改报错信息判断
                current_retry += 1
                logger.error(f"研究信息输入过长，生成最终报告时出错：{e}，当前研究信息长度：{findings_len}，减少 10% 后重试，当前重试次数：{current_retry}......")
                # 后续重试：每次减少10%的研究信息
                findings_len = int(findings_len * 0.9)
                # 截断结果并重试
                findings = findings[:findings_len]
                continue
            else:
                logger.error(f"生成最终报告时出错：{e}......")
                # 非 token 限制错误：立即返回错误
                return {
                    "final_report": f"生成最终报告时出错：{e}",
                    "messages": [AIMessage(content="最终报告生成失败，出现错误")],
                    **cleared_state
                }
    
    # Step 4: 如果所有重试都失败，返回失败结果
    return {
        "final_report": "生成最终报告时出错：最大重试次数已超过",
        "messages": [AIMessage(content="最终报告生成失败，最大重试次数已超过")],
        **cleared_state
    }


# 父图构建，从用户输入到最终报告创建完整的深度研究工作流程
deep_researcher_builder = StateGraph(
    AgentState,  # 定义状态类型，包含所有研究相关的信息，即中间过程信息存储
    input_schema=AgentInputState,  # 设置输入接收的数据类型，接受那些字段
    context_schema=Configuration,  # 配置，RunnableConfig 包含模型设置和偏好的运行时上下文配置，也就是传入运行时定义的字段内容
)

# 父图节点
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)           # 用户澄清阶段
deep_researcher_builder.add_node("write_research_brief", write_research_brief)     # 研究计划阶段
deep_researcher_builder.add_node("research_supervisor", supervisor_subgraph)       # 研究执行阶段
deep_researcher_builder.add_node("final_report_generation", final_report_generation)  # 报告生成阶段

# 父图连接边
deep_researcher_builder.add_edge(START, "clarify_with_user")                       # 入口点
deep_researcher_builder.add_edge("research_supervisor", "final_report_generation") # 研究执行到报告生成
deep_researcher_builder.add_edge("final_report_generation", END)                   # 最终出口点

# 父图编译，生成完整的深度研究工作流
deep_researcher = deep_researcher_builder.compile()

# 生成图片并保存
png_data = deep_researcher.get_graph(xray=True).draw_mermaid_png()
filename = "deep_researcher_graph.png"
with open(filename, "wb") as f:
    f.write(png_data)


async def main(input_state, logger):
    result = await deep_researcher.ainvoke(input_state, context=Configuration(logger=logger))
    print(result)

    # 流式
    # async for chunk in deep_researcher.astream(input_state):
    #     print(chunk)


if __name__ == "__main__":
    topic = "研究最新的AI技术，机器学习方向的最新研究动态，直接开始"
        
    logger = define_log_level(project_root, topic)
    logger.info(f"深度研究主题: {topic}")

    input_state = AgentInputState(
        messages=[HumanMessage(content=topic)]
    )

    import asyncio
    asyncio.run(main(input_state, logger))
