# coding:utf8
from langchain_openai import ChatOpenAI
from zhipuai import ZhipuAI


ZHIPUAI_API_KEY = ''
client = ZhipuAI(api_key=ZHIPUAI_API_KEY)


def zhipu_glm_4(temperature=0.1):
    # 智谱的 temperature 最高不能 >= 1
    model = ChatOpenAI(temperature=temperature, model="glm-4",
                       openai_api_key=ZHIPUAI_API_KEY,
                       openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
                       )
    return model


def glm4_api(prompt):
    try:
        response = client.chat.completions.create(
            model="glm-4-air",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            top_p=0.7,
            temperature=0.95,
            max_tokens=1024,
            tools=[{"type": "web_search", "web_search": {"search_result": True}}],
            stream=False,
        )
    except Exception as e:
        print(e)
        return None
    return response.choices[0].message.content
