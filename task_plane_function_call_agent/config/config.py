# llm opanai 接口用 chat | completions
opanai_chat_switch = True

# qwen 72b
qwen_base_url = ''
qwen_api_ley = ''
qwen_model=""

# llama 70b
llama_base_url = ''
llama_api_key = ''
llama_model = ""

# gpt
gpt_base_url = ''
gpt_api_key = ''
gpt_model = ""

# glm
glm_base_url = 'https://open.bigmodel.cn/api/paas/v4/'
glm_api_key = ''
glm_model = "glm-4-flash"
# glm_model = "glm-zero-preview"

# 大模型定义
from llm.llm_glm import GLM
from llm.llm_qwen import Qwen
from llm.llm_gpt import GPT
from llm.llm_llama import Llama
tp_llm = GLM()
fc_llm = GLM()
# llm = Qwen()
# tp_llm = Llama()
# fc_llm = Llama()
# llm = GPT()
# tp_llm = GPT()
# fc_llm = GPT()

# 项目根路径
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent

# 最大轮数
max_steps = 15

# 任务结束标记
final_label = 'final_answer'

# 可用工具
import json
with open('tool/tools.json', 'r', encoding='utf-8') as f:
    tools = json.load(f)
