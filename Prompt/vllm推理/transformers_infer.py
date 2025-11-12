import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd
import time


path = '/root/autodl-tmp/glm-4-9b-chat'
device = "cuda"

tokenizer = AutoTokenizer.from_pretrained(path,trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True
).to(device).eval()

start_time = time.time()
data = pd.read_csv('data/similary.csv')
data = data.head(100)
for index, row in data.iterrows():
    print(f'{index + 1}\{len(data)}')
    sentence1 = row['sentence1']
    sentence2 = row['sentence2']
    prompt = """
**任务：**
判断两句子（sentence1 和 sentence2）的语义相似度，考虑核心含义、语境、以及可能存在的实体型号差异。

**输出格式：**
严格按照 JSON 格式输出，不要其他任何信息，不要代码，例如：
{{"answer": 1, "reason": "xxxxxxx"}}，{{"answer": 0, "reason": "xxxxxxx"}}

**输入：**
sentence1: {sentence1} 
sentence2: {sentence2}
"""
    inputs = tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                       add_generation_prompt=True,
                                       tokenize=True,
                                       return_tensors="pt",
                                       return_dict=True
                                       )
    inputs = inputs.to(device)
    gen_kwargs = {"max_length": 4096, "do_sample": True, "top_k": 1}
    with torch.no_grad():
        outputs = model.generate(**inputs, **gen_kwargs)
        outputs = outputs[:, inputs['input_ids'].shape[1]:]
        print(tokenizer.decode(outputs[0], skip_special_tokens=True))
end_time = time.time()
print('耗时:', end_time - start_time)
