import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
from langchain_community.llms import Tongyi
from langchain_community.llms import QianfanLLMEndpoint
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import Generation, LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, List, Optional
from transformers import pipeline
from langchain import HuggingFacePipeline


class LLM():

    def __init__(self):
        self.DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
        self.QIANFAN_AK = os.getenv('QIANFAN_AK')
        self.QIANFAN_SK = os.getenv('QIANFAN_SK')

    def tongyi_qwen_plus(self, temperature=1):
        # 通义 qwen_plus
        model = Tongyi(temperature=temperature, model_name='qwen-plus', dashscope_api_key=self.DASHSCOPE_API_KEY)
        return model

    def tongyi_qwen_turbo(self, temperature=1):
        # 通义 qwen-turbo
        model = Tongyi(temperature=temperature, model_name='qwen-turbo', dashscope_api_key=self.DASHSCOPE_API_KEY)
        return model

    def tongyi_qwen_7b_chat(self, temperature=1):
        # 通义 qwen_7b_chat
        model = Tongyi(temperature=temperature, model_name='qwen-7b-chat', dashscope_api_key=self.DASHSCOPE_API_KEY)
        return model

    def tongyi_qwen_14b_chat(self, temperature=1):
        # 通义 qwen_14b_chat
        model = Tongyi(temperature=temperature, model_name='qwen-14b-chat', dashscope_api_key=self.DASHSCOPE_API_KEY)
        return model

    def wenxin_ERNIE_Speed_128K(self):
        # 文心 ERNIE_Speed_128K
        model = QianfanLLMEndpoint(streaming=True, model='ERNIE-Speed-128K', qianfan_ak=self.QIANFAN_AK,
                                   qianfan_sk=self.QIANFAN_SK)
        return model

    def wenxin_ERNIE_Speed_8K(self):
        # 文心 ERNIE_Speed_8K
        model = QianfanLLMEndpoint(streaming=True, model='ERNIE-Speed-8K', qianfan_ak=self.QIANFAN_AK,
                                   qianfan_sk=self.QIANFAN_SK)
        return model

    def wenxin_ERNIE_Speed_AppBuilder(self):
        # 文心 ERNIE Speed-AppBuilder
        model = QianfanLLMEndpoint(streaming=True, model='ERNIE-Speed-8K', qianfan_ak=self.QIANFAN_AK,
                                   qianfan_sk=self.QIANFAN_SK)
        return model

    def wenxin_ERNIE_Lite_8K(self):
        # 文心 ERNIE-Lite-8K
        model = QianfanLLMEndpoint(streaming=True, model='ERNIE-Speed-8K', qianfan_ak=self.QIANFAN_AK,
                                   qianfan_sk=self.QIANFAN_SK)
        return model

    def local_llm(self, model_path, temperature=0.6):
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True).eval()
        model.generation_config = GenerationConfig.from_pretrained(model_path, trust_remote_code=True,
                                                                   temperature=temperature)
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            # max_length=4096,
            # max_tokens=4096,
            max_new_tokens=512,
            top_p=1,
            repetition_penalty=1.15
        )
        model = HuggingFacePipeline(pipeline=pipe)
        return model
