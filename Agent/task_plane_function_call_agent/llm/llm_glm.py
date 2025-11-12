from config.config import glm_base_url, glm_model, glm_api_key, opanai_chat_switch
from openai import OpenAI


class GLM():

    def __init__(self, temperature=0.7, top_p=0.8, max_token=2048, repetition_penalty=1.05):
        self.client = OpenAI(
            api_key=glm_api_key,
            base_url=glm_base_url,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_token = max_token
        self.repetition_penalty = repetition_penalty

    def infer_single(self, prompt):
        if opanai_chat_switch:
            response = self.client.chat.completions.create(
                model=glm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_token,
                extra_body={
                    "repetition_penalty": self.repetition_penalty,
                },
            )
            return response.choices[0].message.content
        else:
            response = self.client.completions.create(
                model=glm_model,
                prompt=prompt,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_token,
                extra_body={
                    "repetition_penalty": self.repetition_penalty,
                },
            )
            return response.choices[0].text

    def infer_tool(self, messages, tools=None):
        response = self.client.chat.completions.create(
            model=glm_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            extra_body={
                "repetition_penalty": self.repetition_penalty,
            },
            tools=tools
        )
        # return response.choices[0].message.content, response.choices[0].message.tool_calls
        return response.choices[0].message

    def infer(self, messages, tools=None):
        response = self.client.chat.completions.create(
            model=glm_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            extra_body={
                "repetition_penalty": self.repetition_penalty,
            },
            tools=tools
        )
        return response.choices[0].message.content



if __name__ == '__main__':
    llm = GLM()
    # print(llm.infer_single("你好"))

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": '我想画一个饼状图来展现我的消费占比,类别为1-2月，1月消费10元，2月消费20元'},
    ]
    tools = [
  {
    "type": "function",
    "function": {
      "name": "pie",
      "description": "根据类别及对应数量数据生成饼状图图",
      "parameters": {
        "type": "object",
        "properties": {
          "labels": {
            "description": "类别标签，列表格式，每个元素为双引号括起来的字符串，英文逗号分隔",
            "type": "array"
          },
          "data": {
            "description": "类别对应数量，列表格式，每个元素为数值，以英文逗号分隔",
            "type": "array"
          }
        },
        "required": [
          "labels",
          "data"
        ],
        "additionalProperties": False
      },
        "strict": True
    }
  }]
    print(llm.infer(messages, tools))


