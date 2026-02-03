from langchain.agents import create_agent
from ChatOpenAIModel_LangChian import ChatOpenAIModel


# Gemini
API_KEY = ""
BASE_URL = ""
MODEL = "gemini-2.5-flash"
extra_body = {
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 0,
            "include_thoughts": True
          }
        }
      }
    }
model = ChatOpenAIModel(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL,
    extra_body=extra_body,
)


def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... email sending logic

    return f"Email sent to {to}"


agent = create_agent(
    model=model,
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
