# coding:utf8
import os
from dotenv import load_dotenv


api_env_path = r'D:\Python_project\NLP\大模型学习\prompt-engineering\key.env'

load_dotenv(api_env_path)
ZHIPUAI_API_KEY = os.getenv('ZHIPUAI_API_KEY')
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
