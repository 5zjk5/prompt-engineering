from config.config import llama_base_url, llama_model, llama_api_key, opanai_chat_switch
from openai import OpenAI


class Llama():

    def __init__(self, temperature=0.7, top_p=0.8, max_token=2048, repetition_penalty=1.2):
        self.client = OpenAI(
            api_key=llama_api_key,
            base_url=llama_base_url,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_token = max_token
        self.repetition_penalty = repetition_penalty

    def infer_single(self, prompt):
        if opanai_chat_switch:
            response = self.client.chat.completions.create(
                model=llama_model,
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
                model=llama_model,
                prompt=prompt,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_token,
                extra_body={
                    "repetition_penalty": self.repetition_penalty,
                },
            )
            return response.choices[0].text

    def infer_tool(self, messages, tools):
        response = self.client.chat.completions.create(
            model=llama_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            extra_body={
                "repetition_penalty": self.repetition_penalty,
            },
            tools=tools,
        )
        # return response.choices[0].message.content, response.choices[0].message.tool_calls
        return response.choices[0].message

    def infer(self, messages, tools=None):
        response = self.client.chat.completions.create(
            model=llama_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            tools=tools
        )
        return response.choices[0].message.content


if __name__ == '__main__':
    llm = Llama()
    # print(llm.infer_single("hello,who are you?"))

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": '我想画一个饼状图来展现我的消费占比,类别为1-2月，1月消费10元，2月消费20元'},
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "pie",
                "description": "根据类别及对应数量数据生成饼图。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "labels": {
                            "description": "类别标签列表。",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "data": {
                            "description": "与类别标签对应的数量列表。",
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        }
                    },
                    "required": ["labels", "data"],
                    # "additionalProperties": False
                },
                # "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pie",
                "description": "根据类别及对应数量数据生成饼图。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "labels": {
                            "description": "类别标签列表。",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "data": {
                            "description": "与类别标签对应的数量列表。",
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        }
                    },
                    "required": ["labels", "data"],
                },
            }
        }
    ]
    print(llm.infer_tool(messages, tools))


