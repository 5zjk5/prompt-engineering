import asyncio
from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, filter_messages
from src.state import ResearcherState, ResearcherOutputState
from src.configuration import Configuration
from src.llm import configurable_model
from src.utils import get_all_tools, get_today_str
from src.prompts import research_system_prompt, compress_research_simple_human_message, compress_research_system_prompt


async def researcher(
    state: ResearcherState, 
    config: RunnableConfig,
    runtime: Runtime[Configuration]
) -> Command[Literal["researcher_tools"]]:
    """
    进行专项研究的研究人员。

    该研究人员由导师分配具体研究课题，并使用现有工具（搜索、think_tool、MCP工具）收集全面信息。它可以在搜索之间使用think_tool进行战略规划。

    参数：
        state：当前研究人员状态，包含消息和课题背景
        config：运行时配置，包含模型设置和工具可用性
        runtime：运行时环境，用于访问配置和上下文
        
    返回值：
        进入researcher_tools执行工具的指令
    """
    logger = runtime.context.logger
    logger.info(f'========== researcher start ==========')

    # Step 1: 加载配置并验证工具可用性
    configurable = Configuration.from_runnable_config(config)
    researcher_messages = state.get("researcher_messages", [])
    
    # 获得所有可用工具 (search, MCP, think_tool)
    tools = await get_all_tools(config)
    if len(tools) == 0:
        raise ValueError(
            "未找到可用于研究的工具：请配置search API或添加MCP工具到您的配置中。"
        )
    logger.info(f'研究者可用工具: {tools}')
    
    # Step 2: 配置研究人员模型与工具
    research_model_config = {
        "tags": ["langsmith:nostream"]
    }
    
    # 如果可用，准备具有MCP上下文的系统提示
    researcher_prompt = research_system_prompt.format(
        mcp_prompt=configurable.mcp_prompt or "", 
        date=get_today_str()
    )
    
    # 使用工具、重试逻辑和设置配置模型
    research_model = (
        configurable_model
        .bind_tools(tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 3: 生成研究者的响应，包含系统上下文
    messages = [SystemMessage(content=researcher_prompt)] + researcher_messages
    response = await research_model.ainvoke(messages)
    logger.info(f'研究者响应:\n {response}')
    
    # Step 4: 更新状态并继续执行工具
    logger.info(f'下一节点：researcher_tools')
    logger.info(f'========== researcher_tools end ==========')
    return Command(
        goto="researcher_tools",
        update={
            "researcher_messages": [response],
            "tool_call_iterations": state.get("tool_call_iterations", 0) + 1
        }
    )


# Tool Execution Helper Function
async def execute_tool_safely(tool, args, config):
    """Safely execute a tool with error handling."""
    try:
        return await tool.ainvoke(args, config)
    except Exception as e:
        return f"Error executing tool: {str(e)}"


async def researcher_tools(
    state: ResearcherState, 
    config: RunnableConfig,
    runtime: Runtime[Configuration]
) -> Command[Literal["researcher", "compress_research"]]:
    """
    执行研究者调用的工具，包括搜索工具和策略性思考。

    该功能处理研究者工具调用：
    1. think_tool — 继续研究对话的策略反思
    2. 搜索工具（tavily_search, web_search） — 信息收集
    3. MCP工具 — 外部工具集成
    4. ResearchComplete — 表示单个研究任务完成

    参数：
    state: 当前研究者状态，包含消息和迭代次数
    config: 运行时配置，包含研究限制和工具设置

    返回：
    命令，用于继续研究循环或进入压缩步骤
    """
    logger = runtime.context.logger
    logger.info(f'========== researcher_tools start ==========')

    # Step 1: 获取当前状态并检查提前退出条件
    configurable = Configuration.from_runnable_config(config)
    researcher_messages = state.get("researcher_messages", [])
    most_recent_message = researcher_messages[-1]
    
    # 如果没有调用工具（包括本地网络搜索），则早期退出
    has_tool_calls = bool(most_recent_message.tool_calls)
    
    if not has_tool_calls:
        logger.info(f'没有调用工具（包括本地网络搜索），开始压缩......')
        logger.info(f'下一节点：compress_research')
        logger.info(f'========== researcher_tools end ==========')
        return Command(goto="compress_research")
    
    # Step 2: 处理其他工具调用（搜索、MCP工具等）
    tools = await get_all_tools(config)
    tools_by_name = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search"): tool 
        for tool in tools
    }
    
    # 并行执行所有工具调用
    tool_calls = most_recent_message.tool_calls
    tool_execution_tasks = [
        execute_tool_safely(tools_by_name[tool_call["name"]], tool_call["args"], config) 
        for tool_call in tool_calls
    ]
    observations = await asyncio.gather(*tool_execution_tasks)
    
    # 根据执行结果创建工具消息
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) 
        for observation, tool_call in zip(observations, tool_calls)
    ]
    
    # Step 3: 检查后期退出条件（处理工具之后）
    exceeded_iterations = state.get("tool_call_iterations", 0) >= configurable.max_react_tool_calls
    research_complete_called = any(
        tool_call["name"] == "ResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )
    
    if exceeded_iterations or research_complete_called:
        logger.info(f'达到退出条件，开始压缩......')
        logger.info(f'下一节点：compress_research')
        logger.info(f'========== researcher_tools end ==========')
        return Command(
            goto="compress_research",
            update={"researcher_messages": tool_outputs}
        )
    
    logger.info(f'下一节点：researcher')
    logger.info(f'========== researcher end ==========')
    return Command(
        goto="researcher",
        update={"researcher_messages": tool_outputs}
    )


async def compress_research(
    state: ResearcherState, 
    config: RunnableConfig,
    runtime: Runtime[Configuration]
):
    """
    将研究成果压缩并整合成简洁、结构化的摘要。
    该函数获取研究者的所有研究成果、工具输出和AI消息，并将其提炼成清晰、全面的摘要，同时保留所有重要信息和发现。

    参数：
        state: 当前研究者的状态，包含累积的研究消息
        config: 运行时配置，包含压缩模型设置
        
    返回值：
        包含压缩研究成果摘要和原始笔记的字典
    """
    logger = runtime.context.logger
    logger.info(f'========== compress_research start ==========')
    
    # Step 1: 配置压缩模型
    configurable = Configuration.from_runnable_config(config)
    synthesizer_model = configurable_model.with_config({
        "tags": ["langsmith:nostream"]
    })
    
    # Step 2: 准备用于压缩的消息
    researcher_messages = state.get("researcher_messages", [])
    
    # 添加指令以从研究模式切换到压缩模式
    researcher_messages.append(HumanMessage(content=compress_research_simple_human_message))
    
    # Step 3: 尝试使用重试逻辑处理令牌限制问题进行压缩
    synthesis_attempts = 0
    max_attempts = 3
    
    while synthesis_attempts < max_attempts:
        try:
            # Create system prompt focused on compression task
            compression_prompt = compress_research_system_prompt.format(date=get_today_str())
            messages = [SystemMessage(content=compression_prompt)] + researcher_messages
            
            # Execute compression
            response = await synthesizer_model.ainvoke(messages)
            
            # Extract raw notes from all tool and AI messages
            raw_notes_content = "\n".join([
                str(message.content) 
                for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
            ])
            
            # Return successful compression result
            return {
                "compressed_research": str(response.content),
                "raw_notes": [raw_notes_content]
            }
            
        except Exception as e:
            synthesis_attempts += 1
            logger.error(f'压缩研究失败，尝试次数 {synthesis_attempts}/{max_attempts}，错误信息: {str(e)}')
            # For other errors, continue retrying
            continue
    
    # Step 4: 果所有尝试都失败，则返回错误结果
    raw_notes_content = "\n".join([
        str(message.content) 
        for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
    ])
    
    logger.info(f'下一节点：END')
    logger.info(f'========== compress_research end ==========')
    return {
        "compressed_research": "研究报告合成错误：最大重试次数超出",
        "raw_notes": [raw_notes_content]
    }


# 研究者子图构建
# 创建针对特定主题进行专注研究的个人研究者工作流
researcher_builder = StateGraph(
    ResearcherState, 
    output_schema=ResearcherOutputState, 
    context_schema=Configuration
)

# 为研究执行和压缩添加研究节点
researcher_builder.add_node("researcher", researcher)                 # 主要研究人员逻辑
researcher_builder.add_node("researcher_tools", researcher_tools)     # 工具执行处理器
researcher_builder.add_node("compress_research", compress_research)   # 研究压缩

# 定义研究人员工作流边
researcher_builder.add_edge(START, "researcher")           # 研究者入口点
researcher_builder.add_edge("compress_research", END)      # 压缩出口点

# 为并行执行由主管编译研究子图
researcher_subgraph = researcher_builder.compile()

# 生成图片并保存
png_data = researcher_subgraph.get_graph(xray=True).draw_mermaid_png()
filename = "researcher_subgraph.png"
with open(filename, "wb") as f:
    f.write(png_data)
