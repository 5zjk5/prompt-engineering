import json
import chromadb
import logging
from utils.embedding_api import EmbeddingAPI
from typing import Dict, Any
from utils.llm_api import LLM
from utils.utils import parse_json
from fastapi import HTTPException


async def tool_description_optimize(tool_json: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    优化工具描述，包括参数描述的优化
    
    Args:
        tool_json: 工具JSON数据
        logger: 日志记录器

    Returns:
        优化后的工具JSON数据
    """
    #region prompt
    promtp = """
你是一个专业的工具描述优化助手。你的任务是根据提供的工具 JSON 定义，生成一段**清晰、准确、结构化且语义完整的功能描述**，用于后续的工具检索与参数理解。

请遵循以下原则：

1. **功能聚焦**：准确概括工具的核心功能，避免泛化或添加未声明的能力。
2. **参数整合**：自然地将关键参数融入描述中，说明其作用，但不罗列。
3. **语言简洁**：使用专业但易懂的中文，避免冗余、模糊或营销性表达。
4. **结构建议**（可选但推荐）：
   - 首句：工具用途总述（动词开头）
   - 中段：关键参数的作用说明（融合在句子中）
   - 结尾：输出或影响说明（如适用）

输入工具：
```json
{tool}
```
输出要求：
仅输出按照原格式优化后的 markdown json，不加解释。
不包含代码块或额外格式。
控制在 1~3 句话内，总长度建议 80~150 字。
输出格式：
```json
{{
    "name": "工具名称",
    "description": "优化后的功能描述",
    "parameters": [
        {{
            "name": "参数名",
            "description": "参数的详细描述"
        }}
    ]
}}
```
    """.strip()
    #endregion

    # 调用LLM优化描述
    llm = LLM(logger=logger)
    optimized_description = await llm.infer(promtp.format(tool=tool_json)) 

    # 解析LLM输出，提取优化后的描述
    optimized_description_parse = parse_json(optimized_description)
    if optimized_description_parse:
        logger.info(f"Optimized tool describe and parse json success: {optimized_description_parse}")
        res_json = optimized_description_parse 
    else:
        logger.info(f"Optimized tool describe success but parse json fail: {optimized_description}")
        res_json = optimized_description

    return res_json


async def insert_tool_to_db(db_path: str, tool_json: Dict[str, Any]) -> None:
    """
    接收db路径及工具json，把name作为id，整个json作为整体向量化入库，集合名为tool_vector
    
    Args:
        db_path: 数据库路径
        tool_json: 工具JSON数据

    Raises:
        HTTPException: 如果ID已存在，提示用户调用更新接口
    """

    # 提取工具名称作为ID
    tool_id = tool_json["name"]
        
    # 连接到Chroma数据库
    client = chromadb.PersistentClient(path=db_path)
        
    # 获取或创建tool_vector集合
    collection = client.get_or_create_collection(name="tool_vector")
    
    # 检查ID是否已存在
    existing_documents = collection.get(ids=[tool_id])
    if existing_documents and existing_documents['ids']:
        raise HTTPException(status_code=409, detail=f"ID '{tool_id}' already exists in the tool_vector collection. Please use the update interface instead.")
        
    # 将整个JSON转换为字符串用于向量化
    tool_content = json.dumps(tool_json, ensure_ascii=False, separators=(',', ':'))
        
    # 初始化向量模型
    embedding_api = EmbeddingAPI()
        
    # 获取工具内容的向量表示
    embedding_result = await embedding_api.get_embedding(tool_content)
        
    # 插入数据到集合中
    collection.add(
        documents=[tool_content],
        embeddings=[embedding_result],
        ids=[tool_id]
    )


async def generate_hypothetical_query(db_path: str, tool_json: Dict[str, Any], logger: logging.Logger) -> None:
    """
    基于工具JSON生成假设查询，插入放到 hypothetical_query 集合
    
    Args:
        db_path: 数据库路径
        tool_json: 工具JSON数据
        logger: 日志记录器

    Returns:
        假设查询
    """
    #region 生成假设查询
    prompt = """
您是生成给定函数可回答的假设性问题的专家。
您将获得一个函数的名称、描述及其参数。
您的工作是执行以下操作：
1. 生成 10 个函数可回答的示例问题。
示例问题中应大约有 50% 包含所有参数，并且读起来类似于教科书类型的问题（例如“如果折现率为 7%，10 年后将收到的 20,000 美元的现值是多少？”）。
而另外 50% 的问题则更抽象，侧重于函数的效用和目的——并且不包含函数参数（例如“我想了解具有盈亏净现值的项目折现率”）。
总体而言，这两种类型的问题应涵盖问题的多样化使用。

以下是一些示例：

--- 

**函数名称：** get_present_value

**描述：**
使用公式 PV = FV / (1 + r)^t 计算未来金额的现值。该函数有助于确定未来现金流的当前价值，考虑了货币的时间价值。适用于评估投资机会、贷款或涉及未来付款的任何财务决策。

**参数：**
- future_value：float，“未来收到或支付的金额。”
- discount_rate：float，“折现率（以小数表示）。”
- periods：int，“支付前的周期数。”

**示例问题：**
- 如果折现率为 7%，10 年后将收到的 20,000 美元的现值是多少？
- 为了在 5 年后获得 50,000 美元，我需要今天投资多少？年折现率为 6%。
- 我想了解一个未来金额的当前价值，我预计会收到它。
- 如果我 15 年后需要 100,000 美元，现在我需要投资多少？假设年回报率为 8%。
- 折现率如何影响我的未来现金流入的现值？

--- 

**函数名称：** get_internal_rate_of_return

**描述：**
计算内部收益率（IRR），即使现金流的净现值（NPV）等于零的折现率。该函数有助于评估潜在投资或项目的盈利能力。在比较多个投资机会以确定哪个回报最高时很有用。

**参数：**
- cash_flows：List[float]，“以初始投资（负值）开头的现金流量序列。”

**示例问题：**
- 初始投资为 50,000 美元，5 年内每年获得 15,000 美元的投资的 IRR 是多少？
- 我如何找到使项目的净现值收支平衡的折现率？
- 我想评估我的投资在数年内的盈利能力。
- 如果我的项目有变化的年度现金流量，我如何确定其内部收益率？
- 我的现金流量在什么利率下变为零？

--- 

**函数名称：** get_future_value

**描述：**
使用复利公式 FV = PV * (1 + r/n)^(n*t) 计算投资的未来价值。该函数有助于投资者确定在特定利率和复利频率下，他们当前的 инвестиция 将随着时间的推移增长多少。适用于规划长期投资、退休基金或储蓄增长。

**参数：**
- present_value：float，“初始投资金额。”
- interest_rate：float，“年利率（以小数表示）。”
- periods：int，“周期数（年）。”
- compounding_frequency：int，“每个周期复利次数。”

**示例问题：**
- 在年利率为 5% 且按季度复利的情况下，5 年后 10,000 美元投资的未来价值是多少？
- 在年利率为 3% 且按月复利的情况下，10 年后我的储蓄将增长到多少？
- 我想了解考虑复利后我的投资在未来是多少。
- 如果我今天投资 5,000 美元，20 年后它在年利率为 7% 且按年复利的情况下将增长到多少？
- 更改复利频率如何影响我的投资的未来价值？

--- 

**函数名称：** get_loan_payment

**描述：**
使用摊销贷款的公式计算分期贷款所需的定期偿还额。该函数有助于借款人了解他们的定期付款义务。适用于规划住房抵押贷款、汽车贷款或任何分期付款的债务偿还。

**参数：**
- principal：float，“借款的贷款总额。”
- annual_interest_rate：float，“年利率（以小数表示）。”
- periods：int，“总付款周期数。”

**示例问题：**
- 一笔 30,000 美元的汽车贷款，年利率为 5%，分 5 年偿还，每月还款额是多少？
- 我需要每月支付多少才能还清我的住房抵押贷款？
- 如果我以 4% 的年利率借了 200,000 美元用于购房，期限为 30 年，我的每月还款额是多少？
- 我想了解我正在考虑的个人贷款的定期还款金额。
- 利率如何影响我的贷款还款金额？

--- 

深呼吸，逐步思考问题，直接输出 10 个示例问题即可，以下是工具的JSON数据：
{tool_json}
    """.strip()
    #endregion
    
    # 提取工具名称作为ID
    tool_id = tool_json["name"]
        
    # 生成假设问题查询
    llm = LLM(logger=logger)
    hypothetical_query = await llm.infer(prompt=prompt.format(tool_json=tool_json))
    logger.info(f"Generate hypothetical query success! hypothetical_query:\n{hypothetical_query}")
    
    # 初始化向量模型
    embedding_api = EmbeddingAPI()
        
    # 获取生成问题向量表示
    embedding_result = await embedding_api.get_embedding(hypothetical_query)
        
    # 连接到Chroma数据库
    client = chromadb.PersistentClient(path=db_path)
        
    # 获取或创建tool_vector集合
    collection = client.get_or_create_collection(name="hypothetical_query")
        
    # 插入数据到集合中
    collection.add(
        documents=[hypothetical_query],
        embeddings=[embedding_result],
        ids=[tool_id]
    )
