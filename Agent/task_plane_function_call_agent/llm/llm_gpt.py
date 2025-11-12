from langchain.chains.question_answering.map_reduce_prompt import messages

from config.config import gpt_base_url, gpt_model, gpt_api_key, opanai_chat_switch
from openai import OpenAI


class GPT():

    def __init__(self, temperature=0.7, top_p=0.8, max_token=2048):
        self.client = OpenAI(
            api_key=gpt_api_key,
            base_url=gpt_base_url,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_token = max_token

    def infer_single(self, prompt):
        """gpt 只能用 chat 接口"""
        response = self.client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
        )
        return response.choices[0].message.content

    def infer_tool(self, messages, tools):
        response = self.client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            tools=tools
        )
        # return response.choices[0].message.content, response.choices[0].message.tool_calls
        return response.choices[0].message

    def infer(self, messages, tools=None):
        response = self.client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_token,
            tools=tools
        )
        return response.choices[0].message.content


if __name__ == '__main__':
    llm = GPT()
    # print(llm.infer_single("你好"))

    # tools = [{
    #     "type": "function",
    #     "function": {
    #         "name": "get_weather",
    #         "description": "Get current temperature for provided coordinates in celsius.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "latitude": {"type": "number"},
    #                 "longitude": {"type": "number"}
    #             },
    #             "required": ["latitude", "longitude"],
    #             "additionalProperties": False
    #         },
    #         "strict": True
    #     }
    # }]
    # messages = [{"role": "user", "content": "What's the weather like in Paris today?"}]
    # print(llm.infer_tool(messages, tools))

    messages = [
        # {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": '我想画一个饼状图来展现我的消费占比,类别为1-2月，1月消费10元，2月消费20元'},
    ]
    tools = [{
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
            "additionalProperties": False
        },
        "strict": True
    }
}]
    print(llm.infer_tool(messages, tools))


