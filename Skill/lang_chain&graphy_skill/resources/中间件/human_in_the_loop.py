# https://docs.langchain.com/oss/python/langchain/middleware#human-in-the-loop
# 在工具调用执行之前，暂停代理执行，以便人工批准、编辑或拒绝。
# 适合：
# 需要人工批准的高风险操作（数据库写入、金融交易）
# 强制人工监督的合规工作流程
# 长时间对话，使用人类反馈来指导代理

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware 
from langgraph.checkpoint.memory import InMemorySaver 
from langchain_core.tools import tool
from langgraph.types import Command
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-pro"
extra_body={
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 512,
            "include_thoughts": True
          }
        }
      }
    }
model = ChatOpenAIModel(
        api_key=API_KEY,
        base_url=BASE_URL,
        extra_body=extra_body,
        model=MODEL,
)


@tool
def write_file_tool(file_path: str, content: str) -> str:
    """写入文件内容到指定路径 write_file"""
    return '文件写入成功'


@tool
def execute_sql_tool(query: str) -> str:
    """执行SQL查询语句 execute_sql"""
    return 'SQL查询执行成功'


@tool
def read_data_tool(data_source: str) -> str:
    """从指定数据源读取数据 read_data"""
    return '数据读取成功'


agent = create_agent(
    model=model,
    tools=[write_file_tool, execute_sql_tool, read_data_tool],
    middleware=[
        HumanInTheLoopMiddleware( 
            interrupt_on={
                "write_file_tool": True,  # 所有决定（批准、编辑、拒绝）均被允许 (approve, edit, reject)
                "execute_sql_tool": {"allowed_decisions": ["approve", "reject"]},  # 不允许编辑，只允许这两个决定
                "read_data_tool": False,  # 安全操作，不需要批准
            },
            # 中断消息的前缀 - 与工具名称和参数结合形成完整消息  
            # 例如："工具执行待批准：execute_sql with query='DELETE FROM...'"  
            # 单个工具可以通过在其中断配置中指定"描述"来覆盖此前缀
            description_prefix="Tool execution pending approval",  # 默认值：“工具执行需要批准”
        ),
    ],
    # 人工参与流程需要设置检查点以处理中断。
    # 在生产环境中，请使用一个持久的检查点存储器，如AsyncPostgresSaver
    checkpointer=InMemorySaver(),  
)

# 人在回路利用LangGraph的持久化层。
# 您必须提供一个线程ID来将执行与对话线程关联，
# 这样对话就可以暂停和继续（这是为了人类审核所必需的）。
config = {"configurable": {"thread_id": "some_id"}} 
result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "执行SQL查询语句：DELETE FROM records WHERE created_at < NOW() - INTERVAL '30 days';",
            }
        ]
    },
    config=config 
)

# 捕获的中断请求 可以将这些操作呈现给审核人员，并在审核人员做出决定后恢复执行。
print(result['__interrupt__'])
# > [
# >    Interrupt(
# >       value={
# >          'action_requests': [
# >             {
# >                'name': 'execute_sql_tool',
# >                'arguments': {'query': 'DELETE FROM records WHERE created_at < NOW() - INTERVAL \'30 days\';'},
# >                'description': 'Tool execution pending approval\n\nTool: execute_sql\nArgs: {...}'
# >             }
# >          ],
# >          'review_configs': [
# >             {
# >                'action_name': 'execute_sql_tool',
# >                'allowed_decisions': ['approve', 'reject']
# >             }
# >          ]
# >       }
# >    )
# > ]


# 审核人员传进来的决策，这里是 approve
res = agent.invoke(
    Command( 
        resume={"decisions": [{"type": "approve"}]}  # or "edit", "reject"
    ), 
    config=config # Same thread ID to resume the paused conversation
)

# 用于edit在执行前修改工具调用。提供修改后的操作、新的工具名称和参数。
agent.invoke(
    Command(
        # 决定以列表形式提供，每个待审核的操作一个。决定的顺序必须与`__interrupt__`请求中列出的操作的顺序相匹配。
        resume={
            "decisions": [
                {
                    "type": "edit",
                    # Edited action with tool name and args
                    "edited_action": {
                        # Tool name to call.
                        # Will usually be the same as the original action.
                        "name": "new_tool_name",
                        # Arguments to pass to the tool.
                        "args": {"key1": "new_value", "key2": "original_value"},
                    }
                }
            ]
        }
    ),
    config=config  # Same thread ID to resume the paused conversation
)

# 用于reject拒绝工具调用并提供反馈而不是执行。
agent.invoke(
    Command(
        # 决定以列表形式提供，每个待审核的操作一个。决定的顺序必须与`__interrupt__`请求中列出的操作的顺序相匹配。
        resume={
            "decisions": [
                {
                    "type": "reject",
                    # An explanation about why the action was rejected
                    "message": "No, this is wrong because ..., instead do this ...",
                }
            ]
        }
    ),
    config=config  # Same thread ID to resume the paused conversation
)

# 当需要审查多个操作时，请按照中断中出现的顺序，对每个操作做出决定：
resume = {
    "decisions": [
        {"type": "approve"},
        {
            "type": "edit",
            "edited_action": {
                "name": "tool_name",
                "args": {"param": "new_value"}
            }
        },
        {
            "type": "reject",
            "message": "This action is not allowed"
        }
    ]
}
