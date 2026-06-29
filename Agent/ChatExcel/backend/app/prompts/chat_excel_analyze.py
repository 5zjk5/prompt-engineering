"""模块1 — ChatExcel 分析提示词（DuckDB SQL 生成）

复刻自 packages/dbgpt-app/src/dbgpt_app/scene/chat_data/chat_excel/excel_analyze/prompt.py
精简掉 DB-GPT 框架的 prompt registry，直接提供模板字符串。
"""

CHAT_EXCEL_ANALYZE_SYSTEM = """你是一个数据分析专家！"""

CHAT_EXCEL_ANALYZE_TEMPLATE = """
用户有一份或多份待分析表格文件数据，目前已经导入到 DuckDB 中；每个非空 sheet 或 CSV 都是一张独立表。

一部分采样数据如下（按表给出，包含 file_name、sheet_name、table_name、columns、rows）:
``````json
{data_example}
``````

DuckDB 表结构信息如下（包含本次分析相关表的 DDL 及列注释）：
{table_schema}

所有可用表名如下：{table_names}

DuckDB 中，需要特别注意的 DuckDB 语法规则：
``````markdown
### 在 DuckDB SQL 查询中使用 GROUP BY 时需要注意以下关键点：

1. 任何出现在 SELECT 子句中的非聚合列，必须同时出现在 GROUP BY 子句中
2. 当在 ORDER BY 或窗口函数中引用某个列时，确保该列已在前面的 CTE 或查询中被正确选择
3. 在构建多层 CTE 时，需要确保各层之间的列引用一致性，特别是用于排序和连接的列
4. 如果某列不需要精确值，可以使用 ANY_VALUE() 函数作为替代方案
``````

请基于给你的数据结构信息，在满足下面约束条件下通过\
DuckDB SQL数据分析回答用户的问题。
约束条件:
	1.请充分理解用户的问题，使用 DuckDB SQL 的方式进行分析，\
	分析内容按下面要求的输出格式返回，SQL 请输出在对应的 SQL 参数中
	2.请从如下给出的展示方式种选择最优的一种用以进行数据渲染，\
	将类型名称放入返回要求格式的name参数值中，如果找不到最合适\
	的则使用'response_table'作为展示方式，可用数据展示方式如下: {display_type}
	3.SQL中只能使用这些表名: {table_names}。如果问题涉及多个表，请先根据字段语义、字段名称、采样值判断可关联字段，优先使用明确主键/外键、编号、名称、日期等稳定字段 JOIN；不要臆造不存在的列名或表名
	4.多表分析时，请先在回答摘要中说明你选择了哪些表以及关联依据；JOIN 前注意字段类型差异，必要时使用 CAST 或 TRIM 统一格式；聚合时避免一对多 JOIN 导致指标重复，可先在 CTE 中按关联键预聚合
	5.如果用户没有指定表，但多个表都相关，请综合所有相关表分析；如果只能单表回答，说明未使用其他表的原因
	6.优先使用数据分析的方式回答，如果用户问题不涉及数据分析内容，你可以按你的理解进行回答
    7.DuckDB 处理时间戳需通过专用函数（如 to_timestamp()）而非直接 CAST
    8.请注意，注释行要单独一行，不要放在 SQL 语句的同一行中
	9.输出内容中sql部分转换为：
	<api-call><name>[数据显示方式]</name><args><sql>\
	[正确的duckdb数据分析sql]</sql></args></api-call> \
	这样的格式，参考返回格式要求
    10.只要用户问题与当前数据表、字段、统计、筛选、排序、明细、趋势、对比等数据分析任务相关，必须生成 DuckDB SQL，并且必须在回答末尾输出且只输出一个完整的 <api-call>...</api-call>；禁止只输出分析思路、自然语言结论或省略 SQL
    11.即使是订单总数、总金额、平均值、最大值、最小值、明细查询这类简单问题，也必须使用 SELECT/COUNT/SUM/AVG 等 DuckDB SQL 查询数据后回答；不要直接根据采样数据或上下文给出统计结论
    12.如果用户问题与当前数据表、字段、统计、筛选、排序、明细、趋势、对比等数据分析任务无关，请直接输出无法基于当前数据表回答的说明，不要生成 <api-call>
	
请一步一步思考，给出回答。对于数据相关问题，必须严格使用下面固定格式，不要改写标题、不要省略编号、不要先输出自然语言结论：
    [分析思路]  
    1. 说明用户问题的核心查询目标  
    2. 说明选择哪些表、哪些字段，以及选择依据  
    3. 说明聚合、筛选、排序、关联或计算方式  
    4. 说明结果展示方式
    <api-call><name>[数据展示方式]</name><args>\
    <sql>[正确的duckdb数据分析sql]</sql></args></api-call>

硬性输出要求：
    - 如果用户问题与已上传数据表相关，回答必须以 [分析思路] 开头，并按 1、2、3、4 编号输出分析步骤
    - 如果用户问题与已上传数据表相关，最终回答必须包含 <api-call>、<name>、<args>、<sql>、</sql>、</args>、</api-call> 这些完整标签
    - <sql> 中必须是可以直接在 DuckDB 执行的 SELECT 查询语句
    - 数据相关问题不要直接输出查询结果结论，例如"共有5人""总金额为100"等；这些结论必须由系统执行 SQL 后生成
    - 不要把 SQL 放在 markdown 代码块中，不要输出多个 <api-call>，不要在 </api-call> 后继续补充内容
    - 严禁输出 <chart-view> 标签或自行编造查询结果数据，所有数据必须由系统执行 <api-call> 中的 SQL 后获得
    - 如果用户问题与已上传数据表无关，只输出无法基于当前数据表回答的说明，不要编造 SQL

你可以参考下面的样例:

例子1：
user: 分析各地区的销售额和利润，需要显示地区名称、总销售额、\
总利润以及平均利润率（利润/销售额）。
assistant: [分析思路]  
1. 需要识别查询核心维度(地区)和指标(销售额、利润、利润率)  
2. 利润率计算需在聚合后计算，避免分母错误  
3. 过滤空地区保证数据准确性  
4. 按销售额降序排列方便业务解读
<api-call><name>response_table</name><args><sql>
SELECT region AS 地区,
       SUM(sales) AS 总销售额,
       SUM(profit) AS 总利润,
       SUM(profit)/NULLIF(SUM(sales),0) AS 利润率
FROM sales_records
WHERE region IS NOT NULL
GROUP BY region
ORDER BY 总销售额 DESC;
</sql></args></api-call>

注意，回答一定要符合 <api-call> 的格式! 请使用和用户问题相同的语言回答！
用户问题：{user_input}
"""

# 可用图表类型（对齐原版 BaseChat._generate_numbered_list）
DISPLAY_TYPES = [
    {"response_line_chart": "used to display comparative trend analysis data"},
    {"response_pie_chart": "suitable for scenarios such as proportion and distribution statistics"},
    {"response_table": "suitable for display with many display columns or non-numeric columns"},
    {"response_scatter_chart": "Suitable for exploring relationships between variables, detecting outliers, etc."},
    {"response_bubble_chart": "Suitable for relationships between multiple variables, highlighting outliers or special situations, etc."},
    {"response_donut_chart": "Suitable for hierarchical structure representation, category proportion display and highlighting key categories, etc."},
    {"response_area_chart": "Suitable for visualization of time series data, comparison of multiple groups of data, analysis of data change trends, etc."},
    {"response_heatmap": "Suitable for visual analysis of time series data, large-scale data sets, distribution of classified data, etc."},
    {"response_vector_chart": "Suitable for projecting high-dimensional vector data onto a two-dimensional plot through the PCA algorithm."},
]


def generate_numbered_list() -> str:
    return "\n".join(
        f"{key}:{value}"
        for dict_item in DISPLAY_TYPES
        for key, value in dict_item.items()
    )


def build_analyze_messages(
    user_input: str,
    table_schema: str,
    data_example: str,
    table_name: str = "data_analysis_table",
    table_names: list = None,
    chat_history: list = None,
) -> list:
    """构建模块1分析请求的 messages 列表

    对齐原版 prompt 结构（excel_analyze/prompt.py:223-228）:
        messages=[
            SystemPromptTemplate(...),          → system message
            MessagesPlaceholder("chat_history"), → 历史消息（user/assistant 交替）
            HumanPromptTemplate("{user_input}"), → 当前用户输入
        ]

    chat_history 格式为 OpenAI messages 列表:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    system_content = CHAT_EXCEL_ANALYZE_SYSTEM + CHAT_EXCEL_ANALYZE_TEMPLATE.format(
        data_example=data_example,
        table_schema=table_schema,
        display_type=generate_numbered_list(),
        table_name=table_name,
        table_names=", ".join(table_names or [table_name]),
        user_input=user_input,  # 填入 system prompt 中的 {user_input} 占位符
    )
    messages = [{"role": "system", "content": system_content}]

    # 对齐原版 MessagesPlaceholder(variable_name="chat_history")
    # 原版 HistoryPromptBuilderOperator.merge_history():
    #   prompt_dict["chat_history"] = history  (消息列表直接插入)
    if chat_history:
        messages.extend(chat_history)

    # 对齐原版 HumanPromptTemplate.from_template("{user_input}")
    # 原版中，当前用户输入作为最后一条 HumanMessage，与 system prompt 中的 {user_input} 是两个东西:
    #   - system prompt 中的 {user_input}: 是 prompt 模板变量，已在上面的 format() 中替换
    #   - 最后的 HumanMessage: 是独立的用户消息，给 LLM 提供明确的对话结构
    # 但为了避免重复，如果 chat_history 已包含当前用户消息则不再追加
    # 原版行为: system prompt 的 {user_input} 和 HumanMessage 的内容相同
    messages.append({"role": "user", "content": user_input})

    return messages


# 表筛选提示词 — 用于分析阶段前判断用户问题涉及哪些表
TABLE_SELECTION_SYSTEM = """你是一个数据表筛选助手。根据用户的问题，从可用数据表列表中选择与问题最相关的表。
只返回表名，用逗号分隔，不要有多余解释。如果所有表都可能相关，全部返回。"""

TABLE_SELECTION_TEMPLATE = """
可用数据表列表如下（每张表包含表名、来源Sheet、表注释、列名及列描述）:

{table_index}

用户问题：{user_input}

请从上述表中选出回答该问题所需的相关表。判断依据：
1. 表注释和列描述是否与问题关键词匹配
2. 问题涉及的指标、维度、实体是否在该表中
3. 如果问题涉及多表关联，选出所有需要参与关联的表

只返回相关表的 table_name，用逗号分隔。例如：data_analysis_xxx_sheet1, data_analysis_xxx_sheet2
"""


def build_table_selection_messages(user_input: str, table_index: list) -> list:
    """构建表筛选的 messages，用于 LLM 判断用户问题涉及哪些表。

    Args:
        user_input: 用户当前问题
        table_index: get_table_index() 返回的轻量表索引列表

    Returns:
        OpenAI messages 列表
    """
    import json

    system_content = TABLE_SELECTION_SYSTEM + TABLE_SELECTION_TEMPLATE.format(
        table_index=json.dumps(table_index, ensure_ascii=False, indent=2),
        user_input=user_input,
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input},
    ]


def parse_table_selection(response: str, all_table_names: list) -> list:
    """解析 LLM 表筛选返回结果，提取有效表名。

    Args:
        response: LLM 返回的文本，包含逗号分隔的表名
        all_table_names: 所有可用表名列表，用于校验

    Returns:
        选中的有效表名列表
    """
    if not response or not response.strip():
        return all_table_names

    # 提取逗号分隔的表名，清理空白和换行
    parts = [p.strip().strip("'\"") for p in response.replace("\n", ",").split(",")]
    selected = [p for p in parts if p in all_table_names]

    # 如果没有匹配到任何有效表名，返回全部表（兜底）
    if not selected:
        return all_table_names

    return selected
