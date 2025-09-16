import pandas as pd
from logs.logger import logger


def read_data(data_path):
    try:
        if '.csv' in data_path:
            try:
                df = pd.read_csv(data_path, encoding='utf-8')
            except:
                df = pd.read_csv(data_path, encoding='gbk')
        elif '.xlsx' in data_path:
            try:
                df = pd.read_excel(data_path, engine='openpyxl')
            except:
                df = pd.read_excel(data_path, engine='xlrd')
        else:
            raise Exception('数据格式错误，只支持csv和xlsx格式')

        # 清理列名 - 去除前后空格和特殊字符
        df.columns = [
            str(col).strip().replace('\n', ' ') if isinstance(col, str) else str(col)
            for col in df.columns
        ]

        # 删除全空行
        df = df.dropna(how='all')

        logger.info(f'读取数据：{data_path}')
        logger.info(f"列名: {list(df.columns)}")
        return df
    except Exception as e:
        import traceback
        error_msg = f"加载数据失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise


def data_random_sample(df, n=50):
    """
    打乱数据取前 n 条，转换为 markdown
    """
    # 随机打乱数据并获取前50条
    df_shuffled = df.sample(frac=1, random_state=None)
    df_head = df_shuffled.head(n)
    logger.info(f"成功读取随机抽样数据，显示前{min(50, len(df))}行")

    # 转换为Markdown表格
    markdown_table = generate_markdown_table(df_head)

    # 添加一些元信息
    markdown_output = f"# Excel数据预览\n\n"
    markdown_output += markdown_table

    return markdown_output


def generate_markdown_table(df):
    """
    将DataFrame转换为Markdown表格

    Parameters:
        df: 要转换的DataFrame

    Returns:
        Markdown格式的表格字符串
    """
    if df.empty:
        return "**没有数据**"

    # 限制列数，避免表格过宽
    if len(df.columns) > 30:
        df = df.iloc[:, :30]
        note = "\n\n*注: 表格仅显示前30列数据，原数据列数过多*"
    else:
        note = ""

    # 处理数据，确保所有值都是字符串且长度适中
    def format_cell(val):
        # 处理None值
        if pd.isna(val):
            return ""

        # 转换为字符串并限制长度
        s = str(val)
        if len(s) > 30:  # 减少单元格最大长度
            return s[:27] + "..."
        return s

    # 手动生成Markdown表格
    headers = df.columns
    header_row = "| " + " | ".join(str(h) for h in headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"

    rows = []
    for _, row in df.iterrows():
        formatted_values = [format_cell(v) for v in row.values]
        row_str = "| " + " | ".join(formatted_values) + " |"
        rows.append(row_str)

    return "\n".join([header_row, separator] + rows) + note
