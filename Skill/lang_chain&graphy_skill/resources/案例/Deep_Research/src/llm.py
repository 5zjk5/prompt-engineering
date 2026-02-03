from src.ChatOpenAIModel_LangChian import ChatOpenAIModel


# Azure LLM
MODEL = "gpt-4.1"
azure_api_version='2025-03-01-preview'
azure_endpoint=""
azure_api_key=""
configurable_model = ChatOpenAIModel(
        model=MODEL,
        use_azure=True,  # 使用微软openai接口
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
)
