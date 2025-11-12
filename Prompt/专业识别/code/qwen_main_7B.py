import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import time
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings


model_path = '/root/autodl-tmp/Qwen-7B-Chat'
embedding_mode_path = '../../model/bge-small-zh-v1.5'

# 加载词表，模型，配置
tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                          trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                             device_map="auto",
                                             trust_remote_code=True).eval()
model.generation_config = GenerationConfig.from_pretrained("/root/autodl-tmp/Qwen-7B-Chat",
                                                           trust_remote_code=True,
                                                           temperature=0.6)  # 可指定不同的生成长度、top_p等相关超参

def prompt_predit(content, labels):
    """prompt 预测 content 属于哪个类别"""
    prompt = f"""找最相关的专业。

请根据以下已知条件：
- 描述：{content}
- 专业列表：{labels}

请遵循以下决策规则：
- 给出的专业必须来自于专业列表中列出的专业。
- 仔细分析描述中出现的专业名词，判断它们是否指向特定的专业。
- 让我们一步一步来思考

请直接回答你认为最相关的专业名称，无需解释说明。
请按照以下格式回答：
- 输出：[专业]

注意：
- 您必须给出回答，不能拒绝回答问题。
- 回答必须简明扼要，不能超出问题所涉及的范围。
"""
    response, history = model.chat(tokenizer, prompt, history=None)
    return response.replace('\n', '').replace(' ', '')


if __name__ == '__main__':
    data = pd.read_csv('../data/classfield_data.csv')
    data = data.head(100)
    with open('../data/labels_all.txt', 'r', encoding='utf8') as f:
        labels = f.readlines()

    embedding = HuggingFaceEmbeddings(model_name=embedding_mode_path)
    db = FAISS.load_local("../data/label_info_vector", embedding, allow_dangerous_deserialization=True)

    res = []
    start_time = time.time()
    for index, row in data.iterrows():
        content = row['content']
        label = row['label']
        label = label.strip('\n')

        print(f'---------- {index + 1} / {len(data)} -----------')
        print(f'当前 content：{content} 正确 label：{label}')
        try:
            # 检索
            top3 = db.similarity_search(content, k=10)
            top3 = [t.page_content.split('\t')[0] for t in top3]

            response = prompt_predit(content, top3)
        except Exception as e:
            response = str(e)
            print(f'解析错误：', response)
        print(f'预测结果：', '=>', response)
        res.append(response)

    data['llm_res'] = res
    # data['correct'] = (data['llm_res'] == data['label'])
    data['correct'] = data.apply(lambda row: True if row['label'] in row['llm_res'] else False, axis=1)
    print(f'预测正确率：', round(sum(data['correct']) / len(data) * 100, 2))
    data.to_excel('../output/classfield_data_predit.xlsx', index=False)

    end_time = time.time()
    print(f'用时：{end_time - start_time}')
