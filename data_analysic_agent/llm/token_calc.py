# coding:utf8
import requests


def token_calc(messages):
    model = 'glm-4-flash'
    api_key = '6e23af3d49a8caa7e976b4ab2ca6c7d2.f5N8QdTbJiYR5nDQ'
    response = requests.post(url="https://open.bigmodel.cn/api/paas/v4/tokenizer",
                             json={"model": model, "messages": messages},
                             headers={"Authorization": api_key})
    response = response.json()
    prompt_tokens = response['usage']['prompt_tokens']
    return prompt_tokens


if __name__ == '__main__':
    message = [
                {
                    "role": "system",
                    "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"
                },
                {
                    "role": "user",
                    "content": 'nihao'
                }
            ]
    print(token_calc(message))
