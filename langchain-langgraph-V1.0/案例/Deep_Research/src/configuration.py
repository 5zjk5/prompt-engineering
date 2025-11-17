import logging
import os
from enum import Enum
from typing import Any, List, Optional
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class SearchAPI(Enum):
    """列出现有的搜索API提供者。"""
    TAVILY = "tavily"
    NONE = "none"


class MCPConfig(BaseModel):
    """模型上下文协议（MCP）服务器的配置。"""
    
    url: Optional[str] = Field(
        default=None,
    )
    """MCP服务器的URL"""
    tools: Optional[List[str]] = Field(
        default=None,
    )
    """LLM可用的工具"""
    auth_required: Optional[bool] = Field(
        default=False,
    )
    """MCP服务器是否需要认证"""


class Configuration(BaseModel):
    """主代理配置类。"""
    
    # 自定义日志
    # logger: ClassVar[logging.Logger] = define_log_level(
    #     project_root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    #     topic="deep_researcher",
    #     print_level="INFO",
    #     logfile_level="DEBUG"
    # )
    logger: Any = Field(
        default=logging.getLogger("deep_researcher"),
        exclude=True
    )  # exclude=True 跳过序列化，方便在 invoke 时传入日志

    # General Configuration
    max_structured_output_retries: int = Field(
        default=3,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 3,
                "min": 1,
                "max": 10,
                "description": "最大结构化输出调用重试次数"
            }
        }
    )
    allow_clarification: bool = Field(
        default=True,
        metadata={
            "x_oap_ui_config": {
                "type": "boolean",
                "default": True,
                "description": "是否允许研究人员在开始研究前向用户询问澄清问题"
            }
        }
    )
    max_concurrent_research_units: int = Field(
        default=5,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 5,
                "min": 1,
                "max": 20,
                "step": 1,
                "description": "最大并发研究单元数量。这将允许研究人员使用多个子代理进行研究。注意：并发数量增加可能会导致速率限制。"
            }
        }
    )
    # Research Configuration
    search_api: SearchAPI = Field(
        default=SearchAPI.TAVILY,
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "tavily",
                "description": "用于研究的搜索API。注意：确保您的研究人员模型支持所选的搜索API。",
                "options": [
                    {"label": "Tavily", "value": SearchAPI.TAVILY.value},
                    {"label": "None", "value": SearchAPI.NONE.value}
                ]
            }
        }
    )
    max_researcher_iterations: int = Field(
        default=3,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 6,
                "min": 1,
                "max": 10,
                "step": 1,
                "description": "研究主管的最大研究迭代次数。这是研究主管将反思研究并询问跟进问题的次数。"
            }
        }
    )
    max_react_tool_calls: int = Field(
        default=3,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 10,
                "min": 1,
                "max": 30,
                "step": 1,
                "description": "研究人员在单个研究步骤中最大工具调用迭代次数。"
            }
        }
    )
    # Model Configuration
    summarization_model: str = Field(
        default="gpt-4.1",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "default": "openai:gpt-4.1-mini",
                "description": "用于总结Tavily搜索结果的研究结果的模型"
            }
        }
    )
    summarization_model_max_tokens: int = Field(
        default=8192,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 8192,
                "description": "总结模型的最大输出令牌数"
            }
        }
    )
    max_content_length: int = Field(
        default=50000,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 50000,
                "min": 1000,
                "max": 200000,
                "description": "研究人员在单个研究步骤中最大字符长度，用于网页内容总结"
            }
        }
    )
    research_model: str = Field(
        default="gpt-4.1",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "default": "gpt-4.1",
                "description": "用于进行研究的模型。注意：确保您的研究人员模型支持所选的搜索API。"
            }
        }
    )
    research_model_max_tokens: int = Field(
        default=10000,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 10000,
                "description": "研究人员模型的最大输出令牌数"
            }
        }
    )
    compression_model: str = Field(
        default="gpt-4.1",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "default": "gpt-4.1",
                "description": "用于压缩子代理研究结果的模型。注意：确保您的压缩模型支持所选的搜索API。"    
            }
        }
    )
    compression_model_max_tokens: int = Field(
        default=8192,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 8192,
                "description": "压缩模型的最大输出令牌数"
            }
        }
    )
    final_report_model: str = Field(
        default="gpt-4.1",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "default": "gpt-4.1",
                "description": "用于编写最终报告的模型，包含所有研究结果"
            }
        }
    )
    final_report_model_max_tokens: int = Field(
        default=10000,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 10000,
                "description": "最终报告模型的最大输出令牌数"
            }
        }
    )
    # MCP server configuration
    mcp_config: Optional[MCPConfig] = Field(
        default=None,
        metadata={
            "x_oap_ui_config": {
                "type": "mcp",
                "description": "MCP服务器配置"
            }
        }
    )
    mcp_prompt: Optional[str] = Field(
        default=None,
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "description": "任何关于MCP工具的额外指令，供Agent使用。"
            }
        }
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建Configuration实例。"""
        configurable = config.get("configurable", {}) if config else {}
        field_names = list(cls.model_fields.keys())
        values: dict[str, Any] = {
            field_name: os.environ.get(field_name.upper(), configurable.get(field_name))
            for field_name in field_names
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

    class Config:
        """Pydantic配置。"""
        arbitrary_types_allowed = True
        