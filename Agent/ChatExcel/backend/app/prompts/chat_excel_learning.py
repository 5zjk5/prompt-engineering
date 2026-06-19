"""模块1 — ChatExcel 学习提示词（首次自动调用，让 LLM 理解数据结构并返回标准 JSON）

完全对齐原版:
- packages/dbgpt-app/src/dbgpt_app/scene/chat_data/chat_excel/excel_learning/prompt.py
- packages/dbgpt-app/src/dbgpt_app/scene/chat_data/chat_excel/excel_learning/out_parser.py

LLM 返回 JSON 格式:
{
    "data_analysis": "数据内容分析总结",
    "column_analysis": [
        {"old_column_name": "原始列名", "new_column_name": "转换后列名", "column_description": "字段说明"},
        ...
    ],
    "analysis_program": ["1.分析方案1", "2.分析方案2", ...]
}
"""

import json

CHAT_EXCEL_LEARNING_SYSTEM = "你是一个数据分析专家. "

CHAT_EXCEL_LEARNING_TEMPLATE = """
给你一份用户的数据, 请你对数据理解并根据下面的要求响应用户，
目前数据在 DuckDB 表中，

一部分采样数据如下:
``````json
{data_example}
``````

表的摘要信息如下:
``````json
{table_summary}
``````

DuckDB 表结构信息如下：
{table_schema}


分析各列数据的含义和作用，并对专业术语进行简单明了的解释, 具体要求：
1. 仔细阅读给你的表结构、数据样例和表摘要信息
2. 提取出字段的列名、数据类型、数据含义、数据格式等信息
3. 为了标准化数据结构数据，我需要对于原来的列名进行转化，如将"年龄"转换为"age", "Completion progress"转化为"completion_progress"等
4. 你需要提供原始的列名、转化后的列名、数据类型、数据含义、数据格式等信息
5. 如果是时间类型请给出时间格式类似:yyyy-MM-dd HH:MM:ss.
6. 请你针对数据从不同维度提供一些有用的分析思路给用户(可以按照分析复杂度从简单到复杂依次提供）
7. 你需要将提取的信息按照下面的格式输出，确保输出的格式正确


列名的转换规则:
1. 如果是英文字母，全部转换为小写，并且将空格替换为下划线
2. 如果是数字，直接保留
3. 如果是中文，将中文字段名翻译为英文，并且将空格替换为下划线
4. 如果是其它语言，将其翻译为英文，并且将空格替换为下划线
5. 如果是特殊字符，直接删除
6. DuckDB遵循SQL标准，要求标识符(列名、表名)不能以数字开头
7. 所有的列字段都必须分析和转换，切记在 JSON 中输出
避免 '// ... (其他列的类似分析) ...' 之类的话术
8. 你需要在json中提供原始列名和转化后的新的列名，以及你分析的该列的含义和作用，如果是时间类型请给出时间格式类似:yyyy-MM-dd HH:MM:ss

你必须输出 JSON 数据，其中:
`data_analysis` 属性是数据内容分析总结，
`column_analysis` 是一个json数组类型，里面包含了每一列的转换、分析结果，
`analysis_program` 属性是分析思路。

请一步一步思考,确保只以JSON格式回答，并且需要能被 Python 的 json.loads() 函数解析。
响应格式如下:
```json
{response}
```
"""

CHAT_EXCEL_LEARNING_USER = "请分析给你的数据"

# 响应格式模板（对齐原版 _RESPONSE_FORMAT_SIMPLE_ZH）
RESPONSE_FORMAT_SIMPLE = {
    "data_analysis": "数据内容分析总结",
    "column_analysis": [
        {
            "old_column_name": "原始列名",
            "new_column_name": "转换后的新的列名",
            "column_description": "字段1介绍，专业术语解释(请尽量简单明了)",
        }
    ],
    "analysis_program": ["1.分析方案1", "2.分析方案2"],
}


def build_learning_messages(
    table_schema: str,
    data_example: str,
    table_summary: str,
    file_name: str,
) -> list:
    """构建学习阶段的 messages（对齐原版 ExcelLearning prompt）"""
    response_str = json.dumps(RESPONSE_FORMAT_SIMPLE, ensure_ascii=False, indent=4)
    system_content = CHAT_EXCEL_LEARNING_SYSTEM + CHAT_EXCEL_LEARNING_TEMPLATE.format(
        table_schema=table_schema,
        data_example=data_example,
        table_summary=table_summary,
        response=response_str,
    )
    user_content = CHAT_EXCEL_LEARNING_USER
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


# ── JSON 解析工具（对齐原版 LearningExcelOutputParser）──────────────────

def parse_learning_response(model_out_text: str) -> dict:
    """解析 LLM 返回的学习 JSON，对齐原版 LearningExcelOutputParser.parse_prompt_response
    
    Returns:
        {
            "data_analysis": str,
            "column_analysis": list[dict],
            "analysis_program": list[str],
        }
    """
    description = ""
    columns = []
    plans = []

    try:
        # 清理 markdown 代码块包裹
        clean_str = model_out_text.strip()
        if clean_str.startswith("```"):
            # 去掉 ```json 和 ``` 包裹
            lines = clean_str.split("\n")
            # 去掉首行 ```json 和末行 ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            clean_str = "\n".join(lines)

        response = json.loads(clean_str)
        for key in sorted(response):
            if key.strip() == "data_analysis":
                description = response[key]
            if key.strip() == "column_analysis":
                columns = response[key]
            if key.strip() == "analysis_program":
                plans = response[key]

        return {
            "data_analysis": description,
            "column_analysis": columns,
            "analysis_program": plans,
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"parse_learning_response failed: {e}")
        # 降级：返回原文作为 data_analysis，列映射为空
        return {
            "data_analysis": model_out_text,
            "column_analysis": [],
            "analysis_program": [],
        }


def build_learning_view_message(data: dict) -> str:
    """构建学习结果的前端展示消息（对齐原版 parse_view_response → Markdown）
    
    格式:
    ### **数据摘要**
    {data_analysis}
    ### **数据结构**
    - **1. new_name(old_name)**: _description_
    - **2. new_name(old_name)**: _description_
    ### **分析建议**
    1. xxx
    2. xxx
    """
    if not data or not isinstance(data, dict):
        return str(data) if data else ""

    # 标题
    file_name = data.get("file_name", "")
    sheet_name = data.get("sheet_name", "")
    title_parts = [part for part in [file_name, sheet_name] if part]
    table_title = f"### **表：{' / '.join(title_parts)}**\n" if title_parts else ""
    html_title = f"{table_title}### **数据摘要**\n{data.get('data_analysis', '')}"

    # 列分析
    columns = data.get("column_analysis", [])
    html_columns = "### **数据结构**\n"
    for idx, item in enumerate(columns, 1):
        new_name = item.get("new_column_name", "")
        old_name = item.get("old_column_name", "")
        desc = item.get("column_description", "")
        html_columns += f"- **{idx}. {new_name}({old_name})**: _{desc}_\n"

    # 分析建议
    plans = data.get("analysis_program", [])
    html_plans = "### **分析建议**\n"
    for plan in plans:
        html_plans += f"{plan}\n"

    return f"{html_title}\n{html_columns}\n{html_plans}"
