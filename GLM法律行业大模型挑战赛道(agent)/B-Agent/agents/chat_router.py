# coding:utf8
from llm.router_chain import router_chain
from llm.glm_llm import zhipu_glm_4
from agents.create_agent import (create_agent_openai_tools, create_agent_plane_execute, agent_prompt,
                                 create_agent_structured_chat)
from tools.company_tools import com_info_tools
from tools.legal_instrument_tools import legal_instrument_tools
from tools.court_tools import court_tools
from tools.law_firms_tools import law_firms_tools
from tools.address_and_weather_tools import address_and_weather_tools
from tools.utils_tools import utils_tools


glm = zhipu_glm_4(temperature=0.5)

all_tools = []
all_tools.extend(utils_tools)
all_tools.extend(com_info_tools)
all_tools.extend(legal_instrument_tools)
all_tools.extend(court_tools)
all_tools.extend(law_firms_tools)
all_tools.extend(address_and_weather_tools)
all_tools.extend(utils_tools)

utils_toolkit = []
utils_toolkit.extend(utils_tools)

company_toolkit = []
company_toolkit.extend(com_info_tools)

legal_instrument_toolkit = []
legal_instrument_toolkit.extend(legal_instrument_tools)

court_toolkit = []
court_toolkit.extend(court_tools)

law_firms_toolkit = []
law_firms_toolkit.extend(law_firms_tools)

address_and_weather_toolkit = []
address_and_weather_toolkit.extend(address_and_weather_tools)


def route(query, agent_type, debug=False):
    info = router_chain.invoke({
        "question": query
    })
    info = info.split('分类结果:')[-1]
    print(f"----- {info} -----")

    # 根据info选择相应的工具包
    toolkits = []
    toolkits_dict = {
        'Company': company_toolkit,
        'Legal Instrument': legal_instrument_toolkit,
        'Court': court_toolkit,
        'Law Firms': law_firms_toolkit,
        'Address and Weather': address_and_weather_toolkit,
    }
    for kind in ['Company', 'Legal Instrument', 'Court', 'Law Firms', 'Address and Weather']:
        if kind.lower() in info.lower():
            toolkits.extend(toolkits_dict[kind])
    toolkits.extend(utils_toolkit)

    # 选择 agent
    if agent_type == 'opanai_tool':
        return create_agent_openai_tools(glm, toolkits, agent_prompt, debug)
    else:
        return create_agent_plane_execute(glm, toolkits, agent_prompt, debug)
