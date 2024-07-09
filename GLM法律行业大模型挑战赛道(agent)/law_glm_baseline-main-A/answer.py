import jsonlines
from tqdm import tqdm

from llm.check_llm_response import template
from llm.glm_llm import glm4_api
from utils import read_jsonl

from agents.chat_router import route


def answer(query: str):
    agent = route(query)

    messages = agent.invoke({"messages": [("human", query)]})
    return messages


if __name__ == '__main__':
    question_file = "./data/questions/question.jsonl"
    # 修改输出文件
    result_file = "data/results/result_fix.json"
    queries = read_jsonl(question_file)

    # 生成答案
    print("Start generating answers...")

    for query in tqdm(queries):
        # 如果中断，可以从这里开始
        if query["id"] not in [148]:
            continue
        response = answer(query["question"])
        # status = glm4_api(template.format(question=query["question"], answer=response))
        # if status == "No":
        if response["output"].endswith("：") or "<|assistant|>搜索引擎/search" in response["output"] or "tool_call" in \
                response["output"] or "目前没有" in response["output"]:
            response = glm4_api(query["question"])
            content = {
                "id": query["id"],
                "question": query["question"],
                "answer": response
            }
        else:
            content = {
                "id": query["id"],
                "question": query["question"],
                "answer": response["output"]
            }
        print(response)
        with jsonlines.open(result_file, "a") as json_file:
            json_file.write(content)
