from ChatOpenAIModel_LangChian import model
from langchain_core.tools import tool
from langchain.agents import create_agent
from sub_agent import calendar_agent, email_agent
from langgraph.checkpoint.memory import InMemorySaver 
from langgraph.types import Command


@tool
def schedule_event(request: str) -> str:
    """使用自然语言安排日历事件。

    当用户想要创建、修改或检查日历约会时使用此工具。
    处理日期/时间解析、可用性检查和事件创建。

    输入：自然语言日程安排请求（例如，'与设计团队下周二下午2点开会'）
    """
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


@tool
def manage_email(request: str) -> str:
    """使用自然语言发送电子邮件。

    当用户想要发送通知、提醒或任何电子邮件通信时使用此工具。
    处理收件人提取、主题生成和电子邮件撰写。

    输入：自然语言电子邮件请求（例如，'向他们发送关于会议的提醒'）
    """
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


SUPERVISOR_PROMPT = (
    "你是一个有用的个人助理。"
    "你可以安排日历事件和发送电子邮件。"
    "将用户请求分解为适当的工具调用并协调结果。"
    "当一个请求涉及多个操作时，按顺序使用多个工具。"
)

supervisor_agent = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt=SUPERVISOR_PROMPT,
    checkpointer=InMemorySaver(),
)

# 单智能体
# query = "为明天上午9点安排一次团队站会"
# for step in supervisor_agent.stream(
#     {"messages": [{"role": "user", "content": query}]}
# ):
#     for update in step.values():
#         for message in update.get("messages", []):
#             message.pretty_print()

# 多智能体
# 创建日历跟撞见邮件需要中断，人工审批
interrupts = []
config = {"configurable": {"thread_id": "6"}}
query = "下周二下午2点安排与设计团队开会，持续1小时，并给他们发邮件提醒评审新模型。"
for step in supervisor_agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    config
):
    for update in step.values():
        if isinstance(update, dict):
            for message in update.get("messages", []):
                message.pretty_print()
        else:
            interrupt_ = update[0]
            interrupts.append(interrupt_)
            print(f"\nINTERRUPTED: {interrupt_.id}")

# 检查中断事件
print(f'\n查看中断事件：')
for interrupt_ in interrupts:
    for request in interrupt_.value["action_requests"]:
        print(f"INTERRUPTED: {interrupt_.id}")
        print(f"{request['description']}\n")


# 接受日历事件，编辑外发邮件的主题
resume = {}
for interrupt_ in interrupts:
    if interrupt_.id == "邮件编辑中断id":
        # Edit email
        edited_action = interrupt_.value["action_requests"][0].copy()
        edited_action["arguments"]["subject"] = "Mockups reminder"
        resume[interrupt_.id] = {
            "decisions": [{"type": "edit", "edited_action": edited_action}]
        }
    else:
        resume[interrupt_.id] = {"decisions": [{"type": "approve"}]}
interrupts = []
for step in supervisor_agent.stream(
    Command(resume=resume), 
    config,
):
    for update in step.values():
        if isinstance(update, dict):
            for message in update.get("messages", []):
                message.pretty_print()
        else:
            interrupt_ = update[0]
            interrupts.append(interrupt_)
            print(f"\nINTERRUPTED: {interrupt_.id}")
