import json
import io
import requests
import copy
import time
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from logs.logger import logger


@dataclass
class PreprocessingConfig:
    drop_na: bool = False
    date_columns: List[str] = None
    date_format: str = "%Y-%m-%d"  # 修改为标准的Python日期格式


@dataclass
class SortConfig:
    column: str
    ascending: bool = True


@dataclass
class DimensionConfig:
    name: str
    dimension_column: str
    metrics_columns: List[str]
    aggregation_methods: Dict[str, str]
    group_by_columns: List[str] = None
    sort_by: Optional[SortConfig] = None
    top_n: Optional[int] = None  # 将默认为None，代码中会处理为总行数
    filters: Dict[str, Any] = None


@dataclass
class TimeSeriesConfig:
    enabled: bool = False
    time_column: Optional[str] = None
    frequency: str = "M"
    metrics: List[str] = None
    aggregation: str = "sum"


@dataclass
class CorrelationConfig:
    enabled: bool = False
    columns: List[str] = None
    method: str = "pearson"


@dataclass
class AnalysisConfig:
    analysis_id: str
    analysis_name: str
    preprocessing: PreprocessingConfig
    dimensions: List[DimensionConfig]
    time_series_analysis: TimeSeriesConfig = None
    correlation_analysis: CorrelationConfig = None


class DataAnalyzer:
    def __init__(self, config_json: str, data: pd.DataFrame):
        """初始化数据分析器
        Args:
            config_json: 配置JSON字符串，维度字符串
        """
        self.config_json = config_json
        self.config = None  # 将在load_data后设置
        self.df = data
        self.results = {}

    def _download_file_with_retry(self, url, max_retries=3, timeout=60, chunk_size=8192):
        """使用分块下载和重试机制下载文件"""
        from requests.exceptions import RequestException

        for attempt in range(max_retries):
            try:
                logger.info(f"尝试下载文件 (尝试 {attempt + 1}/{max_retries})...")

                # 设置超时和流式传输
                session = requests.Session()
                # 增加连接池大小和保持连接
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=5,
                    pool_maxsize=20,
                    max_retries=3
                )
                session.mount('http://', adapter)
                session.mount('https://', adapter)

                # 发送HEAD请求检查文件大小
                try:
                    head_response = session.head(url, timeout=timeout / 2)
                    head_response.raise_for_status()
                    total_size = int(head_response.headers.get('content-length', 0))
                    if total_size:
                        logger.info(f"文件大小: {total_size / 1024 / 1024:.2f} MB")
                except Exception as e:
                    logger.info(f"检查文件大小失败: {str(e)}，继续下载...")
                    total_size = 0

                # 开始下载
                response = session.get(url, stream=True, timeout=timeout)
                response.raise_for_status()

                # 如果HEAD请求未获取到大小，从GET响应获取
                if not total_size:
                    total_size = int(response.headers.get('content-length', 0))
                    if total_size:
                        logger.info(f"文件大小: {total_size / 1024 / 1024:.2f} MB")

                # 使用字节IO流收集数据
                content = bytearray()
                downloaded = 0

                # 分块下载
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤掉保持连接alive的空块
                        content.extend(chunk)
                        downloaded += len(chunk)

                        # 每下载1MB记录一次进度
                        if downloaded % (1024 * 1024) == 0 and total_size:
                            progress = (downloaded / total_size) * 100
                            logger.info(
                                f"下载进度: {progress:.1f}% ({downloaded / 1024 / 1024:.2f}/{total_size / 1024 / 1024:.2f} MB)")

                logger.info(f"文件下载完成，总大小: {len(content) / 1024 / 1024:.2f} MB")
                return bytes(content)

            except RequestException as e:
                logger.error(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    # 指数退避策略
                    wait_time = 2 ** attempt
                    logger.warning(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error("达到最大重试次数，下载失败")
                    raise

    def _parse_config(self, config_json: str, available_columns: List[str] = None) -> AnalysisConfig:
        """解析配置JSON字符串，并根据可用列名进行智能匹配
        Args:
            config_json: 配置JSON字符串
            available_columns: 可用的列名列表
        Returns:
            解析后的配置对象
        """
        try:
            config_dict = json.loads(config_json)  # 非标 json 会报错
        except:
            config_dict = eval(config_json)
        logger.info(f'解析维度配置：\n{config_json}')

        # 如果有可用列名，进行智能匹配
        if available_columns:
            config_dict = self._auto_match_columns(config_dict, available_columns)

        logger.info(f'开始转换预处理，维度，时间序列，相关性分析配置')

        # 转换预处理配置
        preprocessing = PreprocessingConfig(**config_dict['preprocessing'])

        # 转换维度配置
        dimensions = []
        for dim_dict in config_dict['dimensions']:
            if 'sort_by' in dim_dict and dim_dict['sort_by']:
                dim_dict['sort_by'] = SortConfig(**dim_dict['sort_by'])
            dimensions.append(DimensionConfig(**dim_dict))

        # 转换时间序列配置
        time_series = None
        if 'time_series_analysis' in config_dict and config_dict['time_series_analysis']:
            time_series = TimeSeriesConfig(**config_dict['time_series_analysis'])

        # 转换相关性分析配置
        correlation = None
        if 'correlation_analysis' in config_dict and config_dict['correlation_analysis']:
            correlation = CorrelationConfig(**config_dict['correlation_analysis'])

        return AnalysisConfig(
            analysis_id=config_dict['analysis_id'],
            analysis_name=config_dict['analysis_name'],
            preprocessing=preprocessing,
            dimensions=dimensions,
            time_series_analysis=time_series,
            correlation_analysis=correlation
        )

    def _auto_match_columns(self, config_dict: Dict, available_columns: List[str]) -> Dict:
        """智能匹配配置中的列名与实际列名"""
        logger.info(f'开始智能匹配列名，更新配置 json...')
        available_columns = [str(col) for col in available_columns]
        updated_config = copy.deepcopy(config_dict)

        # 更新维度配置
        for dim_config in updated_config.get('dimensions', []):
            # 匹配维度列
            dim_col = dim_config.get('dimension_column')
            if dim_col and dim_col not in available_columns:
                matched_col = self._find_similar_column(dim_col, available_columns)
                if matched_col:
                    logger.info(f"将维度列 '{dim_col}' 匹配为 '{matched_col}'")
                    dim_config['dimension_column'] = matched_col

            # 匹配指标列
            metrics = dim_config.get('metrics_columns', [])
            agg_methods = dim_config.get('aggregation_methods', {})
            for i, metric in enumerate(metrics):
                if metric not in available_columns:
                    matched_col = self._find_similar_column(metric, available_columns)
                    if matched_col:
                        logger.info(f"将指标列 '{metric}' 匹配为 '{matched_col}'")
                        # 更新指标列
                        metrics[i] = matched_col
                        # 更新聚合方法
                        if metric in agg_methods:
                            agg_methods[matched_col] = agg_methods.pop(metric)

        # 更新时间序列配置
        ts_config = updated_config.get('time_series_analysis', {})
        if ts_config.get('enabled', False):
            time_col = ts_config.get('time_column')
            if time_col and time_col not in available_columns:
                matched_col = self._find_similar_column(time_col, available_columns)
                if matched_col:
                    logger.info(f"将时间列 '{time_col}' 匹配为 '{matched_col}'")
                    ts_config['time_column'] = matched_col

        # 更新相关性分析配置
        corr_config = updated_config.get('correlation_analysis', {})
        if corr_config.get('enabled', False):
            corr_columns = corr_config.get('columns', [])
            for i, col in enumerate(corr_columns):
                if col not in available_columns:
                    matched_col = self._find_similar_column(col, available_columns)
                    if matched_col:
                        logger.info(f"将相关性分析列 '{col}' 匹配为 '{matched_col}'")
                        corr_columns[i] = matched_col

        return updated_config

    def _find_similar_column(self, target: str, available_columns: List[str]) -> Optional[str]:
        """查找与目标列名最相似的列"""
        if not target or not isinstance(target, str):
            return None

        # 1. 精确匹配（忽略大小写）
        for col in available_columns:
            if str(col).lower() == target.lower():
                return col

        # 2. 包含匹配
        contained_matches = [col for col in available_columns
                             if target.lower() in str(col).lower() or str(col).lower() in target.lower()]
        if contained_matches:
            return contained_matches[0]

        # 3. 简单相似度匹配
        max_similarity = 0
        best_match = None
        for col in available_columns:
            # 计算简单相似度（共同字符比例）
            common_chars = set(str(col).lower()) & set(target.lower())
            similarity = len(common_chars) / max(len(set(str(col).lower())), len(set(target.lower())))
            if similarity > max_similarity and similarity > 0.5:  # 相似度阈值
                max_similarity = similarity
                best_match = col

        return best_match

    def _detect_header_row(self, excel_content: bytes) -> int:
        """自动检测表头行"""
        # 常见的表头关键字
        header_keywords = ["序号", "时间", "日期", "姓名", "名称", "金额", "数量", "地址", "电话", "联系方式", "出单",
                           "保单", "备注", "情况"]
        best_row = 0
        max_matches = 0

        # 尝试不同的行作为表头
        for i in range(10):  # 检查前10行
            try:
                df = pd.read_excel(io.BytesIO(excel_content), header=i, nrows=1)  # 只读取一行来检测
                columns = [str(col).lower() for col in df.columns]

                # 计算匹配的关键字数量
                matches = sum(1 for keyword in header_keywords
                              if any(keyword.lower() in str(col).lower() for col in columns))

                # 如果匹配度更高，更新最佳行
                if matches > max_matches:
                    max_matches = matches
                    best_row = i
            except Exception as e:
                logger.error(f"检测表头第{i + 1}行时出错: {str(e)}")
                continue

        logger.info(f"自动检测到表头在第{best_row + 1}行，匹配关键字数量: {max_matches}")
        return best_row

    def preprocess_data(self):
        """数据预处理"""
        # 根据实际列名解析配置
        logger.info(f'解析分析维度 json......')
        self.config = self._parse_config(self.config_json, list(self.df.columns))
        prep_config = self.config.preprocessing

        # 重要修改：不要使用drop_na，而是有选择地处理缺失值
        # 如果配置中设置了drop_na，我们只在这里记录，但不执行全局删除
        if prep_config.drop_na:
            logger.info("注意: 已禁用全局drop_na，将针对特定列处理缺失值")

        # 处理日期列
        logger.info(f'处理日期列，转换为 pandas datetime格式......')
        if prep_config.date_columns:
            for col in prep_config.date_columns:
                if col in self.df.columns:
                    try:
                        # 首先尝试自动转换
                        self.df[col] = pd.to_datetime(self.df[col], errors='coerce')

                        # 检查是否有成功转换的日期
                        if self.df[col].notna().any():
                            logger.info(f"成功将'{col}'列转换为日期格式")
                        else:
                            logger.info(f"警告: '{col}'列所有值都转换失败")

                        # 记录一些统计信息
                        logger.info(f"{col}列的非空值数量: {self.df[col].notna().sum()}")
                        logger.info(f"{col}列的空值数量: {self.df[col].isna().sum()}")
                        if self.df[col].notna().any():
                            logger.info(f"{col}列的最早日期: {self.df[col].min()}")
                            logger.info(f"{col}列的最晚日期: {self.df[col].max()}")
                    except Exception as e:
                        logger.error(f"警告: 转换日期列 '{col}' 时出错: {str(e)}")

        # 检查并转换数值列
        logger.info(f'检查并转换数值列，把是数值的指标列转换为数值类型......')
        for dim_config in self.config.dimensions:
            for metric in dim_config.metrics_columns:
                if metric in self.df.columns:
                    # 检查数据类型
                    logger.info(f"{metric}列的数据类型: {self.df[metric].dtype}")
                    logger.info(f"{metric}列的缺失值数量: {self.df[metric].isna().sum()}")
                    logger.info(f"{metric}列的前5个值:\n {self.df[metric].head()}")

                    # 转换为数值类型，如果这一列都是数字那才转换，否则有文本字符串不转换
                    try:
                        col_data = self.df[metric]
                        for value in col_data:
                            float(value)  # 成功则为数字
                        self.df[metric] = pd.to_numeric(self.df[metric], errors='coerce')
                        logger.info(f"已将{metric}列转换为数值类型")
                    except Exception as e:
                        logger.warning(f"警告: 转换{metric}列为数值类型时出错: {str(e)}")

                    # 填充缺失值为0
                    self.df[metric] = self.df[metric].fillna(0)

        # 检查维度列的唯一值
        logger.info(f'检查维度列的唯一值......')
        for dim_config in self.config.dimensions:
            dim_col = dim_config.dimension_column
            if dim_col in self.df.columns:
                unique_values = self.df[dim_col].unique()
                logger.info(f"{dim_col}列的唯一值: {unique_values}")
                logger.info(f"{dim_col}列的缺失值数量: {self.df[dim_col].isna().sum()}")

                # 重要修改：确保维度列没有空值，用"未知"填充
                self.df[dim_col] = self.df[dim_col].fillna("未知")

        logger.info("数据预处理完成")
        return self

    def _apply_filters(self, df, filters):
        """应用过滤条件"""
        if not filters:
            return df

        filtered_df = df.copy()
        for column, condition in filters.items():
            if column not in filtered_df.columns:
                logger.info(f"警告: 过滤列 '{column}' 不存在，跳过此过滤条件")
                continue

            if isinstance(condition, list):
                filtered_df = filtered_df[filtered_df[column].isin(condition)]
            elif isinstance(condition, dict):
                if 'min' in condition:
                    filtered_df = filtered_df[filtered_df[column] >= condition['min']]
                if 'max' in condition:
                    filtered_df = filtered_df[filtered_df[column] <= condition['max']]
            else:
                filtered_df = filtered_df[filtered_df[column] == condition]

        return filtered_df

    def _generate_markdown_table(self, df):
        """生成Markdown表格"""
        if df.empty:
            return "**没有数据**"

        # 手动生成Markdown表格，因为to_markdown可能不可用
        headers = df.columns
        header_row = "| " + " | ".join(str(h) for h in headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"

        rows = []
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(v) for v in row.values) + " |"
            rows.append(row_str)

        return "\n".join([header_row, separator] + rows)

    def analyze_dimension(self, dim_config):
        """分析单个维度"""
        logger.info(f"开始分析维度: {dim_config.name}")

        # 检查维度列是否存在
        if dim_config.dimension_column not in self.df.columns:
            error_msg = f"错误: 维度列 '{dim_config.dimension_column}' 不存在"
            logger.info(error_msg)
            return {
                "name": dim_config.name,
                "error": error_msg,
                "markdown": f"**{error_msg}**\n\n可用列: {list(self.df.columns)}"
            }

        # 检查指标列是否存在
        for metric in dim_config.metrics_columns:
            if metric not in self.df.columns:
                error_msg = f"错误: 指标列 '{metric}' 不存在"
                logger.info(error_msg)
                return {
                    "name": dim_config.name,
                    "error": error_msg,
                    "markdown": f"**{error_msg}**\n\n可用列: {list(self.df.columns)}"
                }

        # 应用过滤条件
        filtered_df = self._apply_filters(self.df, dim_config.filters)

        # 处理指标列中的缺失值
        for col in dim_config.metrics_columns:
            if pd.api.types.is_numeric_dtype(filtered_df[col]):
                filtered_df[col] = filtered_df[col].fillna(0)

        # 打印分组前的数据样例
        logger.info("分组前数据样例:")
        logger.info(filtered_df[[dim_config.dimension_column] + dim_config.metrics_columns].head())

        # 重要修改：检查是否有数据
        if filtered_df.empty:
            error_msg = "过滤后没有数据可分析"
            logger.info(error_msg)
            return {
                "name": dim_config.name,
                "error": error_msg,
                "markdown": f"**{error_msg}**"
            }

        # 准备分组列
        group_cols = [dim_config.dimension_column]
        if dim_config.group_by_columns:
            for col in dim_config.group_by_columns:
                if col in filtered_df.columns:
                    group_cols.append(col)
                else:
                    logger.info(f"警告: 分组列 '{col}' 不存在，将被忽略")

        # 执行聚合
        agg_dict = dim_config.aggregation_methods
        try:
            # 确保维度列不为空
            filtered_df = filtered_df.dropna(subset=[dim_config.dimension_column])

            # 打印分组和聚合信息
            logger.info(f"分组列: {group_cols}")
            logger.info(f"聚合方法: {agg_dict}")

            try:
                # 重要修改：直接使用pandas的pivot_table，更可靠地处理分组聚合
                result_df = pd.pivot_table(
                    filtered_df,
                    index=group_cols,
                    values=list(agg_dict.keys()),
                    aggfunc=agg_dict,
                    fill_value=0
                ).reset_index()
            except Exception as e:
                logger.warning(f'pivot_table 聚合函数失败，尝试 value_counts 替换为 counts 聚合函数')
                if 'value_counts' in agg_dict.values():
                    for k, v in agg_dict.items():
                        if v == 'value_counts':
                            agg_dict[k] = 'count'
                    result_df = pd.pivot_table(
                        filtered_df,
                        index=group_cols,
                        values=list(agg_dict.keys()),
                        aggfunc=agg_dict,
                        fill_value=0
                    ).reset_index()
                else:
                    raise '尝试 value_counts 替换为 counts 聚合函数 error'

            # 打印分组结果
            logger.info("分组聚合结果:")
            logger.info(result_df)

            # 重要修改：检查结果是否为空
            if result_df.empty:
                error_msg = "聚合后没有数据"
                logger.info(error_msg)
                return {
                    "name": dim_config.name,
                    "error": error_msg,
                    "markdown": f"**{error_msg}**"
                }
        except Exception as e:
            error_msg = f"聚合分析失败: {str(e)}"
            logger.error(error_msg)

            # 重要修改：尝试使用更简单的方法进行分组
            try:
                logger.info("尝试使用简化方法进行分组...")
                # 简单地计算每个维度值的指标总和
                result_data = []
                for dim_value in filtered_df[dim_config.dimension_column].unique():
                    row_data = {dim_config.dimension_column: dim_value}
                    for metric in dim_config.metrics_columns:
                        subset = filtered_df[filtered_df[dim_config.dimension_column] == dim_value]
                        row_data[metric] = subset[metric].sum()
                    result_data.append(row_data)

                result_df = pd.DataFrame(result_data)
                logger.info("简化分组结果:")
                logger.info(result_df)

                if result_df.empty:
                    return {
                        "name": dim_config.name,
                        "error": error_msg,
                        "markdown": f"**{error_msg}**"
                    }
            except:
                return {
                    "name": dim_config.name,
                    "error": error_msg,
                    "markdown": f"**{error_msg}**"
                }

        # 排序
        if dim_config.sort_by:
            sort_col = dim_config.sort_by.column
            if sort_col in result_df.columns:
                result_df = result_df.sort_values(
                    by=sort_col,
                    ascending=dim_config.sort_by.ascending
                )
                logger.info(f"已按{sort_col}列{'升序' if dim_config.sort_by.ascending else '降序'}排序")
            else:
                logger.warning(f"警告: 排序列 '{sort_col}' 不存在，跳过排序")

        # 取Top N - 如果未指定，则使用全部行数
        if dim_config.top_n is not None:
            result_df = result_df.head(dim_config.top_n)
            logger.info(f"已取前{dim_config.top_n}行数据")

        # 生成Markdown表格
        markdown_table = self._generate_markdown_table(result_df)
        return {
            "name": dim_config.name,
            "markdown": markdown_table
        }

    def analyze_time_series(self):
        """时间序列分析"""
        ts_config = self.config.time_series_analysis
        if not ts_config or not ts_config.enabled:
            return None

        logger.info("开始时间序列分析")

        # 确保时间列存在
        if ts_config.time_column not in self.df.columns:
            error_msg = f"错误: 时间列 {ts_config.time_column} 不存在"
            logger.info(error_msg)
            return {
                "name": "时间序列分析",
                "error": error_msg,
                "markdown": f"**{error_msg}**\n\n可用列: {list(self.df.columns)}"
            }

        try:
            # 创建副本避免修改原始数据
            df_ts = self.df.copy()

            # 确保时间列是日期类型
            df_ts[ts_config.time_column] = pd.to_datetime(df_ts[ts_config.time_column], errors='coerce')

            # 删除时间列为空的行
            df_ts = df_ts.dropna(subset=[ts_config.time_column])

            if df_ts.empty:
                return {
                    "name": "时间序列分析",
                    "error": "没有有效的日期数据",
                    "markdown": "**错误: 没有有效的日期数据**"
                }

            # 处理指标列
            for metric in ts_config.metrics:
                if metric not in df_ts.columns:
                    continue
                df_ts[metric] = pd.to_numeric(df_ts[metric], errors='coerce')
                df_ts[metric] = df_ts[metric].fillna(0)

            # 设置时间索引
            df_ts = df_ts.set_index(ts_config.time_column)

            # 按频率重采样
            agg_dict = {metric: ts_config.aggregation for metric in ts_config.metrics}
            resampled = df_ts.resample(ts_config.frequency).agg(agg_dict)

            # 重置索引并格式化日期
            result_df = resampled.reset_index()
            result_df[ts_config.time_column] = result_df[ts_config.time_column].dt.strftime('%Y-%m-%d')

            # 生成Markdown表格
            markdown_table = self._generate_markdown_table(result_df)
            return {
                "name": "时间序列分析",
                "markdown": markdown_table
            }

        except Exception as e:
            error_msg = f"时间序列分析失败: {str(e)}"
            logger.error(error_msg)
            return {
                "name": "时间序列分析",
                "error": error_msg,
                "markdown": f"**{error_msg}**"
            }

    def analyze_correlation(self):
        """相关性分析"""
        corr_config = self.config.correlation_analysis
        if not corr_config or not corr_config.enabled:
            return None

        logger.info("开始相关性分析")

        # 检查相关性列是否存在
        missing_cols = [col for col in corr_config.columns if col not in self.df.columns]
        if missing_cols:
            error_msg = f"错误: 相关性分析列不存在: {missing_cols}"
            logger.info(error_msg)
            return {
                "name": "相关性分析",
                "error": error_msg,
                "markdown": f"**{error_msg}**\n\n可用列: {list(self.df.columns)}"
            }

        try:
            # 确保所有列都是数值类型
            corr_df = self.df[corr_config.columns].copy()
            for col in corr_config.columns:
                corr_df[col] = pd.to_numeric(corr_df[col], errors='coerce')

            # 打印相关性数据样例
            logger.info("相关性分析数据样例:")
            logger.info(corr_df.head())

            # 计算相关性
            corr_matrix = corr_df.corr(method=corr_config.method)
            logger.info("相关性矩阵:")
            logger.info(corr_matrix)

            # 重置索引，便于生成Markdown表格
            corr_result = corr_matrix.reset_index().rename(columns={'index': '变量'})

            # 生成Markdown表格
            markdown_table = self._generate_markdown_table(corr_result)
            return {
                "name": "相关性分析",
                "markdown": markdown_table
            }
        except Exception as e:
            error_msg = f"相关性分析失败: {str(e)}"
            logger.error(error_msg)
            return {
                "name": "相关性分析",
                "error": error_msg,
                "markdown": f"**{error_msg}**"
            }

    def run_analysis(self):
        """执行所有分析"""
        # 预处理数据
        logger.info("开始数据预处理......")
        self.preprocess_data()

        # 分析各个维度
        logger.info("✅ 数据预处理完成，开始数据维度分析......")
        dimension_results = []
        for dim_config in self.config.dimensions:
            result = self.analyze_dimension(dim_config)
            dimension_results.append(result)

        # 时间序列分析
        time_series_result = self.analyze_time_series()

        # 相关性分析
        correlation_result = self.analyze_correlation()

        # 汇总结果
        self.results = {
            "analysis_id": self.config.analysis_id,
            "analysis_name": self.config.analysis_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dimensions": dimension_results,
            "time_series": time_series_result,
            "correlation": correlation_result
        }

        return self.results
