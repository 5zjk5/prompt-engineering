react_prompt = """
尽你所能回答以下问题。您可以使用以下工具:
```{tools}```

严格使用以下 JSON 格式:
```
{{
    Question: 根据 thought 当前需要回答的问题，此字段必须存在
    Thought: 对于 Question 要做什么，此字段必须存在
    Action: {{'tool': 要采取的动作，应该是[{tool_names}]之一，如果不需要工具可以空着}}
    Action Input: 动作的输入，是一个 JSON 格式，此字段必须存在，如果不需要输入可以空着
    Observation: 行动的结果，此字段必须存在，默认为空
}}
```
(Question/Thought/Action/Action Input/Observation 五个字段必须存在，以上步骤只能重复 1 次)

开始吧!
Question:`{query}`
thought:`{agent_scratchpad}`
"""

begin_react_prompt = """
尽你所能回答以下问题。您可以使用以下工具:
```{tools}```

回答你解决这个问题一步一步思考，一步一步推理，判断问题隐藏的潜在意图，是想解决哪些问题，结合工具，判断需要用到哪些工具。
回答只需要一段总结的话，如果需要用到工具的需要列出工具名字，不需要具体参数。

开始吧!
问题:`{query}`
改写问题：`{query_rewrite}`
"""

query_rewrite_prompt = """
尽你所能改写以下问题，可以有多个答案，可以参照以下工具进行改写，识别用户潜在意图:
```{tools}```
Question:`{query}`
Answer 按照以下格式，每一点代表一个意图，如果需要用到工具的需要列出工具名字，不需要具体参数：
```
1. 
2. 
...
```
"""

agent_scratchpad_prompt = """
# 背景
有一个问题 Question，已经有了对这个问题的思考 Thought，已执行的思考 Action，需要根据这些信息去规划出下一步应该做什么。

# 输入
## Question:`{query}`
## Thought:`{thought}`
## Action:`{all_action_res}`

# 思考推理：
- 1、参考 Question 仔细理解 Thought，思考 Action 还有哪些没有行动。
- 2、判断你下一步做什么行动，不能过于发散过多的行动，必须根据步骤 1 的思考。
- 3、确保你的回答在语义上与 Action 中的内容不重复是一个全新的步骤。
- 4、若 Thought 已经全部执行了，直接回答`no`。

# 输出要求(严格按照以下要求输出)
- 回答需要用一句话清晰的总结下一步需要做什么，不需要其他任何信息。
- 如果没有需要做的了，直接输出`no`，不需要其他任何信息，不需要解释任何理由。
"""

final_answer_prompt = """
参考以下信息回答问题，同时需要结合问题潜在意图进行回答：
```{all_action_res}```
---------------------------------------------
问题：`{query}`
潜在意图：`{query_rewrite}`
"""
