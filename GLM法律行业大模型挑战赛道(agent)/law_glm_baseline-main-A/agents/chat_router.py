from llm.glm_llm import glm
from llm.router_chain import router_chain
from agents.create_agent import create_agent, company_prompt, law_prompt
from tools import com_info_tools, com_register_tools, sub_com_info_tools, law_tools

all_tools = []

all_tools.extend(com_info_tools)
all_tools.extend(com_register_tools)
all_tools.extend(sub_com_info_tools)
all_tools.extend(law_tools)

company_toolkit = []
company_toolkit.extend(com_info_tools)
company_toolkit.extend(com_register_tools)
company_toolkit.extend(sub_com_info_tools)

law_toolkit = []

law_toolkit.extend(law_tools)


def route(query, debug=False):
    info = router_chain.invoke({
        "question": query
    })
    if debug:
        print(f"----- {info} -----")

    # 根据info选择相应的工具包
    if "company" == info.lower():
        return create_agent(glm, company_toolkit, company_prompt)
    elif "law" == info.lower():
        return create_agent(glm, law_toolkit, law_prompt)
    else:
        return create_agent(glm, all_tools)
