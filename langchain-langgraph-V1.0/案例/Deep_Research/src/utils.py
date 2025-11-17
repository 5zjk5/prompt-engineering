from datetime import datetime
from langchain_core.messages import MessageLikeRepresentation, filter_messages
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from src.tools import ResearchComplete, think_tool, tavily_search
from src.configuration import Configuration, SearchAPI


def get_today_str() -> str:
    """
    获取用于提示和输出的当前日期格式化字符串。

    返回：人类可读的日期字符串，格式类似于'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"


def get_notes_from_tool_calls(messages: list[MessageLikeRepresentation]):
    """从工具调用消息中提取笔记。"""
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]


async def get_all_tools(config: RunnableConfig):
    """
    组装包括研究、搜索和MCP工具的完整工具包。

    参数：
        config：指定搜索API和MCP设置的运行时配置

    返回值：
        用于研究操作的所有配置且可用的工具列表
    """
    # 以核心研究工具开始
    tools = [tool(ResearchComplete), think_tool]
    
    # 添加配置的搜索工具
    configurable = Configuration.from_runnable_config(config)
    search_api = SearchAPI(get_config_value(configurable.search_api))
    search_tools = await get_search_tool(search_api)
    tools.extend(search_tools)
    
    # 跟踪现有工具名称，以防止冲突
    existing_tool_names = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search") 
        for tool in tools
    }
    
    # 添加MCP工具（如果配置了）
    pass
    
    return tools


def get_config_value(value):
    """从配置中提取值，处理枚举和None值。"""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return value
    else:
        return value.value


async def get_search_tool(search_api: SearchAPI):
    """
    根据指定的 API 提供商配置并返回搜索工具。

    Args:
        search_api: 要使用的搜索 API 提供商（Anthropic、OpenAI、Tavily 或 None)
        
    Returns:
        指定提供者的配置搜索工具对象列表
    """ 
    if search_api == SearchAPI.TAVILY:
        # 配置Tavily搜索工具的元数据
        search_tool = tavily_search
        search_tool.metadata = {
            **(search_tool.metadata or {}), 
            "type": "search", 
            "name": "web_search"
        }
        return [search_tool]
        
    elif search_api == SearchAPI.NONE:
        # 未配置搜索功能
        return []
        
    # 未知的搜索 API 类型默认回退
    return []
