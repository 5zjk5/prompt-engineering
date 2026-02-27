
# https://langfuse.com/docs/observability/get-started
"""
langchain 最基本使用
"""
import os
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI  
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv as load_env


# Load environment variables
load_env()

# Initialize Langfuse client with constructor arguments
Langfuse(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    host=os.getenv('LANGFUSE_BASE_URL')  
)

# Get the configured client instance
langfuse = get_client()

# Initialize the Langfuse handler
langfuse_handler = CallbackHandler()

# Create your LangChain components
llm = ChatOpenAI(
    model=os.getenv('model'),
    base_url=os.getenv('base_url'),
    api_key=os.getenv('api_key'),
)
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
chain = prompt | llm

# Run your chain with Langfuse tracing
response = chain.invoke({"topic": "cats"}, config={"callbacks": [langfuse_handler]})
print(response.content)

# Flush events to Langfuse in short-lived applications
langfuse.flush()
