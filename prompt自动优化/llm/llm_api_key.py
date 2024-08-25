# coding:utf8
import os
from dotenv import load_dotenv
from config.config import api_env_path


load_dotenv(api_env_path)
ZHIPUAI_API_KEY = os.getenv('ZHIPUAI_API_KEY')
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
