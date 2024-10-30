import os
import warnings
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
warnings.filterwarnings('ignore')

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
import pandas as pd
import time


class vllmModel():

    def __init__(self, model_path, temperature=0.1, max_tokens=4096, tp_size=1):
        """
        model_path: 模型路径
        temperature: 温度
        max_tokens: 模型最大输出 token
        tp_size: gpu 数量，可以为 1 张卡卡，多余一张卡，必须是双数，如 2,4,6
        """
        print(f'加载本地模型：{model_path}')
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.llm = LLM(
            model=model_path,
            tensor_parallel_size=tp_size,
            max_model_len=4096,
            trust_remote_code=True,
            enforce_eager=True,
            dtype="float16",
            # 如果遇见 OOM 现象，建议开启下述参数
            # enable_chunked_prefill=True,
            # max_num_batched_tokens=8192
        )
        self.sampling_params = SamplingParams(temperature=temperature, max_tokens=max_tokens)
        print("模型加载完毕")

    def infer(self, prompts):
        """
        prompts: prompt 列表
        """
        prompts = [{"role": "user", "content": prompt} for prompt in prompts]
        inputs = []
        for prompt in prompts:
            _input = self.tokenizer.apply_chat_template([prompt], tokenize=False, add_generation_prompt=True)
            inputs.append(_input)
        outputs = self.llm.generate(prompts=inputs, sampling_params=self.sampling_params)
        result = []
        for output in outputs:
            text = output.outputs[0].text
            result.append(text)
        return result


# 加载模型
model_path = "/root/autodl-tmp/glm-4-9b-chat"
llm = vllmModel(model_path)

# 测试数据
batch = 64
start_time = time.time()
data = pd.read_csv('data/similary.csv')
data = data.head(100)
result = []
for i in range(0, len(data), batch):
    batchc_df = data.iloc[i:i + batch, :]
    batch_prompt = []
    for index, row in batchc_df.iterrows():
        sentence1 = row['sentence1']
        sentence2 = row['sentence2']
        prompt = """
**任务：**
判断两句子（sentence1 和 sentence2）的语义相似度，考虑核心含义、语境、以及可能存在的实体型号差异。

**输入：**
sentence1: {sentence1} 
sentence2: {sentence2}

**输出格式：**
严格按照 JSON 格式输出，不要其他任何信息，不要代码，例如：
{{"answer": 1, "reason": "xxxxxxx"}}，{{"answer": 0, "reason": "xxxxxxx"}}
"""
        batch_prompt.append(prompt.format(sentence1=sentence1, sentence2=sentence2))
    res = llm.infer(batch_prompt)
    result.extend(res)
end_time = time.time()
print('耗时:', end_time - start_time)
