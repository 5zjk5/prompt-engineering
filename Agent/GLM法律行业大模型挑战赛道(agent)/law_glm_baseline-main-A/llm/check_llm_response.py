"""
@Time : 2024/6/26 16:15 
@Author : sunshb10145 
@File : check_llm_response.py 
@desc:
"""
template = """To classify whether an answer correctly addresses a given question, classify it as either being about `Yes` or `No`.

Do not respond with more than one word.

<question>
{question}
</question>

<answer>
{answer}
</answer>

Classification:"""