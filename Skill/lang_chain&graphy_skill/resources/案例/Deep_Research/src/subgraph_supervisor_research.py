import asyncio
from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain_core.messages import ToolMessage, HumanMessage
from src.configuration import Configuration
from src.state import SupervisorState
from src.tools import ConductResearch, ResearchComplete, think_tool
from src.llm import configurable_model
from src.utils import get_notes_from_tool_calls
from src.subgraph_researcher import researcher_subgraph


async def supervisor(
    state: SupervisorState, 
    config: RunnableConfig, 
    runtime: Runtime[Configuration]
) -> Command[Literal["supervisor_tools"]]:
    """
    首席研究督导负责规划研究策略并分配给研究人员。

    督导分析研究简报，决定如何将研究分解为可管理任务。
    可以使用think_tool进行战略规划，
    使用ConductResearch将任务分配给子研究人员，
    或当对研究结果满意时使用ResearchComplete。

    参数：
        state：当前督导状态，包含消息和研究上下文
        config：运行时配置，包含模型设置
        runtime：运行时环境，用于访问配置和上下文

    返回：
        命令，用于进入supervisor_tools进行工具执行
    """
    logger = runtime.context.logger
    logger.info(f'========== supervisor start ==========')

    # Step 1: 使用可用工具配置监督模型
    configurable = Configuration.from_runnable_config(config)
    research_model_config = {
        "tags": ["langsmith:nostream"]
    }
    
    # 现有工具：研究小组、完成信号和战略思维
    lead_researcher_tools = [ConductResearch, ResearchComplete, think_tool]
    
    # 使用工具配置模型、重试逻辑和模型设置
    research_model = (
        configurable_model
        .bind_tools(lead_researcher_tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 2: 根据当前情境生成监控员响应
    supervisor_messages = state.get("supervisor_messages", [])
    response = await research_model.ainvoke(supervisor_messages)
    logger.info(f"研究指导战略规划结果:\n{response}")
    
    # Step 3: 更新状态，继续进行工具执行
    logger.info(f'开始第 {state.get("research_iterations", 0) + 1} 轮迭代研究')
    logger.info(f'下一节点：supervisor_tools')
    logger.info(f'========== supervisor end ==========')
    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )


async def supervisor_tools(
    state: SupervisorState, 
    config: RunnableConfig,
    runtime: Runtime[Configuration]
) -> Command[Literal["supervisor", "__end__"]]:
    """
    此功能处理三种类型的主管工具调用：
    1. think_tool - 继续对话的战略反思
    2. ConductResearch - 将研究任务委派给子研究者
    3. ResearchComplete - 信号研究阶段完成

    参数：
        state: 当前主管状态，包含消息和迭代次数
        config: 运行时配置，包含研究限制和模型设置

    返回值：
        继续主管循环或结束研究阶段的指令
    """
    logger = runtime.context.logger
    logger.info(f'========== supervisor_tools start ==========')

    # Step 1: 提取当前状态并检查退出条件
    configurable = Configuration.from_runnable_config(config)
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]
    
    # 定义研究阶段的退出标准
    exceeded_allowed_iterations = research_iterations > configurable.max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete_tool_call = any(
        tool_call["name"] == "ResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )
    logger.info(f'\n达到最大迭代次数={exceeded_allowed_iterations}, \n是否没有工具调用了={no_tool_calls}, \n是否都是研究完成工具调用={research_complete_tool_call}')
    
    # 如果满足任何终止条件，则退出
    if exceeded_allowed_iterations or no_tool_calls or research_complete_tool_call:
        logger.info(f'满足任意条件，退出研究阶段！')
        logger.info(f'下一节点：END')
        logger.info(f'========== supervisor end ==========')
        return Command(
            goto=END,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    
    # Step 2: 将所有工具调用一起处理（包括 think_tool 和 ConductResearch）
    all_tool_messages = []
    update_payload = {"supervisor_messages": []}
    
    # 处理think_tool调用（战略反思）
    think_tool_calls = [
        tool_call for tool_call in most_recent_message.tool_calls 
        if tool_call["name"] == "think_tool"
    ]
    
    for tool_call in think_tool_calls:
        reflection_content = tool_call["args"]["reflection"]
        all_tool_messages.append(ToolMessage(
            content=f"反思已记录：{reflection_content}",
            name="think_tool",
            tool_call_id=tool_call["id"]
        ))
    
    # 处理ConductResearch调用（研究委派），即搜索
    conduct_research_calls = [
        tool_call for tool_call in most_recent_message.tool_calls 
        if tool_call["name"] == "ConductResearch"
    ]
    
    if conduct_research_calls:
        try:
            logger.info(f'存在 {len(conduct_research_calls)} 个 ConductResearch 工具调用，即搜索......')

            # 限制并发研究单元以防止资源耗尽
            allowed_conduct_research_calls = conduct_research_calls[:configurable.max_concurrent_research_units]
            overflow_conduct_research_calls = conduct_research_calls[configurable.max_concurrent_research_units:]
            logger.info(f'允许并发搜索任务数 {configurable.max_concurrent_research_units}，\n溢出搜索任务数 {len(overflow_conduct_research_calls)}')
            
            # 并行执行研究任务
            research_tasks = [
                researcher_subgraph.ainvoke({
                    "researcher_messages": [
                        HumanMessage(content=tool_call["args"]["research_topic"])
                    ],
                    "research_topic": tool_call["args"]["research_topic"]
                }, config) 
                for tool_call in allowed_conduct_research_calls
            ]
            
            tool_results = await asyncio.gather(*research_tasks)
            logger.info(f'成功完成 {len(tool_results)} 个 ConductResearch 工具调用，即搜索任务......')
            
            # 创建基于研究成果的工具消息
            for observation, tool_call in zip(tool_results, allowed_conduct_research_calls):
                all_tool_messages.append(ToolMessage(
                    content=observation.get("compressed_research", "研究报告合成错误：最大重试次数已超过"),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                ))
            
            # 处理溢出研究调用并返回错误消息
            for overflow_call in overflow_conduct_research_calls:
                all_tool_messages.append(ToolMessage(
                    content=f"错误：已超过最大并发研究单元数。请再次尝试使用最多 {configurable.max_concurrent_research_units} 个研究单元。",
                    name="ConductResearch",
                    tool_call_id=overflow_call["id"]
                ))
            
            # 聚合所有研究结果的原始笔记
            raw_notes_concat = "\n".join([
                "\n".join(observation.get("raw_notes", [])) 
                for observation in tool_results
            ])
            
            if raw_notes_concat:
                logger.info(f'更新研究搜索结果，共 {len(tool_results)} 条笔记')
                update_payload["raw_notes"] = [raw_notes_concat]
                
        except Exception as e:
            logger.error(f'ConductResearch 工具调用异常：{e}')
            logger.info(f'下一节点：END')
            logger.info(f'========== supervisor end ==========')
            return Command(
                goto=END,
                update={
                    "notes": get_notes_from_tool_calls(supervisor_messages),
                    "research_brief": state.get("research_brief", "")
                }
            )
    
    # Step 3: 返回包含所有工具结果的命令
    update_payload["supervisor_messages"] = all_tool_messages
    logger.info(f'supervisor_messages 更新 {len(all_tool_messages)} 条消息')
    logger.info(f'下一节点：supervisor')
    logger.info(f'========== supervisor_tools end ==========')
    return Command(
        goto="supervisor",
        update=update_payload
    ) 


# 创建监督工作流，管理研究委派与协调
supervisor_builder = StateGraph(
    SupervisorState,
    context_schema=Configuration
)

# 监督子图节点
supervisor_builder.add_node("supervisor", supervisor)           # 主监督逻辑
supervisor_builder.add_node("supervisor_tools", supervisor_tools)  # 工具执行处理

# 监督子图边
supervisor_builder.add_edge(START, "supervisor")  # 入口点到监督逻辑

# 监督子图编译
supervisor_subgraph = supervisor_builder.compile()

# 生成图片并保存
png_data = supervisor_subgraph.get_graph(xray=True).draw_mermaid_png()
filename = "supervisor_subgraph.png"
with open(filename, "wb") as f:
    f.write(png_data)
