from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from llm.glm_llm import glm

template = """Given the user question below, classify it as either being about `Company` or `Law`.
    
Do not respond with more than one word.

<question>
{question}
</question>

Classification:"""

router_chain = (
        PromptTemplate.from_template(template)
        | glm
        | StrOutputParser()
)
