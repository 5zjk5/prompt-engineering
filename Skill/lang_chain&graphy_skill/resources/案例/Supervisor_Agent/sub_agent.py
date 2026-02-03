from ChatOpenAIModel_LangChian import model
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain.agents.middleware import HumanInTheLoopMiddleware 


@tool
def create_calendar_event(
    title: str,
    start_time: str,       # ISO format: "2024-01-15T14:00:00"
    end_time: str,         # ISO format: "2024-01-15T15:00:00"
    attendees: list[str],  # email addresses
    location: str = ""
) -> str:
    """创建日历事件。需要精确的ISO日期时间格式。"""
    # Stub: In practice, this would call Google Calendar API, Outlook API, etc.
    return f"Event created: {title} from {start_time} to {end_time} with {len(attendees)} attendees"


@tool
def send_email(
    to: list[str],  # email addresses
    subject: str,
    body: str,
    cc: list[str] = []
) -> str:
    """通过电子邮件API发送电子邮件。需要正确格式的地址。"""
    # Stub: In practice, this would call SendGrid, Gmail API, etc.
    return f"Email sent to {', '.join(to)} - Subject: {subject}"


@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int
) -> list[str]:
    """检查特定日期给定参与者的日历可用性。"""
    # Stub: In practice, this would query calendar APIs
    return ["09:00", "14:00", "16:00"]


CALENDAR_AGENT_PROMPT = (
    "你是一个日历安排助理。"
    "将自然语言日程安排请求（例如，'下周二下午2点'）"
    "解析为正确的ISO日期时间格式。"
    "在需要时使用get_available_time_slots检查可用性。"
    "使用create_calendar_event安排事件。"
    "在最终回复中始终确认已安排的内容。"
)

calendar_agent = create_agent(
    model,
    tools=[create_calendar_event, get_available_time_slots],
    system_prompt=CALENDAR_AGENT_PROMPT,
    middleware=[ 
        HumanInTheLoopMiddleware( 
            interrupt_on={"create_calendar_event": True}, 
            description_prefix="Calendar event pending approval", 
        ), 
    ], 
)

EMAIL_AGENT_PROMPT = (
    "你是一个电子邮件助理。"
    "根据自然语言请求撰写专业电子邮件。"
    "提取收件人信息并制作适当的主题行和正文。"
    "使用send_email发送消息。"
    "在最终回复中始终确认已发送的内容。"
)

email_agent = create_agent(
    model,
    tools=[send_email],
    system_prompt=EMAIL_AGENT_PROMPT,
    middleware=[ 
        HumanInTheLoopMiddleware( 
            interrupt_on={"send_email": True}, 
            description_prefix="Outbound email pending approval", 
        ), 
    ], 
)
