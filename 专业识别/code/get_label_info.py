from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig


# 加载词表，模型，配置
tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                          trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                             device_map="auto",
                                             trust_remote_code=True).eval()
model.generation_config = GenerationConfig.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                                           trust_remote_code=True,
                                                           temperature=0.6)

with open('../data/labels_all.txt', 'r', encoding='utf8') as f:
    lines = f.readlines()

# 生成标签描述
infos = []
for line in lines:
    line = line.strip('\n')
    prompt = f"""
    你是一位对各个专业都有研究的学者，擅长区分不同的专业，弄了个介绍每个专业的特点。
    现在我已有有了一些专业名称，请你根据专业名称，说出这个专业的特点，介绍一下，字数不超过50个字。
    以下是专业名称：`{line}`"""
    response, history = model.chat(tokenizer, prompt, history=None)
    print(f'{line}-{response}')
    infos.append([line, response])

# 保存标签描述
with open('../data/label_info.txt', 'w', encoding='utf8') as f:
    for info in infos:
        f.write(info[0] + '\t' + info[1] + '\n')
        print(info)
