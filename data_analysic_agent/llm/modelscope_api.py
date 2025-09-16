from openai import OpenAI


client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1/',
    api_key='ce42db5a-54c7-4e8f-adf0-1ab1f44a73cc', # ModelScope Token
)


def modelscope_api(messages, temperature=0.6, model='Qwen/Qwen3-32B', enable_thinking=False):
    if isinstance(messages, str):
        messages = [
            {
                "role": "user",
                "content": messages
            }
        ]

    extra_body = {
        # enable thinking, set to False to disable
        "enable_thinking": enable_thinking,
        # use thinking_budget to contorl num of tokens used for thinking
        # "thinking_budget": 4096
    }
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        extra_body=extra_body
    )
    content = ''
    reasoning = ''
    for chunk in response:
        reasoning += chunk.choices[0].delta.reasoning_content
        content += chunk.choices[0].delta.content
    return content


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
    print(modelscope_api(message, enable_thinking=False))
