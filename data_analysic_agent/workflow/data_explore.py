import ast
import re
import asyncio
from utils.utils import read_data, data_random_sample
from logs.logger import logger
from llm.modelscope_api import modelscope_api
from prompt.analysis_dimension import analysis_dimension_prompt
from prompt.analysis_conclusion import analysis_conclusion_prompt
from workflow.analysis_dimension import DataAnalyzer
from workflow.img_create import ImageCreate
from workflow.generate_report import GenerateReport


class DataExplore:

    def __init__(self, data_path, query):
        self.data_path = data_path
        self.data = read_data(self.data_path)
        self.query = query

    def run(self):
        # 随机取 50 条数据，转换为 markdown
        markdown_output = data_random_sample(self.data)
        logger.info(f"""【开始运行】✅ 数据读取完成；读取到{len(self.data)}条有效数据""")

        # 生成数据分析维度
        # profiles_list = general_analysis_dimension(markdown_output, self.query)
        profiles_list = [
            {'analysis_id': 'school_distribution_by_province', 'analysis_name': '按省份划分的高校分布分析',
             'correlation_analysis': {'columns': [], 'enabled': False}, 'dimensions': [
                {'aggregation_methods': {'学校': 'count'}, 'dimension_column': '省份', 'metrics_columns': ['学校'],
                 'name': '省份分布统计', 'sort_by': {'ascending': False, 'column': '学校_count'}}],
             'preprocessing': {'date_columns': [], 'date_format': '', 'drop_na': False},
             'time_series_analysis': {'aggregation': '', 'enabled': False, 'frequency': '', 'metrics': [],
                                      'time_column': ''}},
            {'analysis_id': 'school_type_distribution', 'analysis_name': '按办学类型划分的高校分布分析',
             'correlation_analysis': {'columns': [], 'enabled': False}, 'dimensions': [
                {'aggregation_methods': {'学校': 'count'}, 'dimension_column': '办学类型', 'metrics_columns': ['学校'],
                 'name': '办学类型分布', 'sort_by': {'ascending': False, 'column': '学校_count'}}],
             'preprocessing': {'date_columns': [], 'date_format': '', 'drop_na': False},
             'time_series_analysis': {'aggregation': '', 'enabled': False, 'frequency': '', 'metrics': [],
                                      'time_column': ''}},
            {'analysis_id': 'school_level_and_category', 'analysis_name': '高校层次与类别组合分析',
             'correlation_analysis': {'columns': [], 'enabled': False}, 'dimensions': [
                {'aggregation_methods': {'办学类别': 'value_counts'}, 'dimension_column': '水平层次',
                 'metrics_columns': ['办学类别'], 'name': '水平层次与办学类别组合',
                 'sort_by': {'ascending': False, 'column': '办学类别_value_counts'}}],
             'preprocessing': {'date_columns': [], 'date_format': '', 'drop_na': False},
             'time_series_analysis': {'aggregation': '', 'enabled': False, 'frequency': '', 'metrics': [],
                                      'time_column': ''}},
            {'analysis_id': 'province_city_school_distribution', 'analysis_name': '省份-城市维度下的高校分布分析',
             'correlation_analysis': {'columns': [], 'enabled': False}, 'dimensions': [
                {'aggregation_methods': {'城市': 'nunique', '学校': 'count'}, 'dimension_column': '省份',
                 'metrics_columns': ['城市', '学校'], 'name': '省份与城市组合分布',
                 'sort_by': {'ascending': False, 'column': '学校_count'}}],
             'preprocessing': {'date_columns': [], 'date_format': '', 'drop_na': False},
             'time_series_analysis': {'aggregation': '', 'enabled': False, 'frequency': '', 'metrics': [],
                                      'time_column': ''}}]  # todo debug
        logger.info(f"数据分析维度生成完成，共 {len(profiles_list)} 个维度")

        # 维度分析
        logger.info("正在分析维度.....")
        results = []
        for index, profile in enumerate(profiles_list):
            logger.info(f"正在分析维度 {index + 1}/{len(profiles_list)}: {profile['analysis_name']}")
            result = analysis_dimension(profile, self.data)
            results.append(result)
        logger.info(f'✅ 数据清洗完成.....')

        # 图表绘制
        logger.info(f'正在绘制图表....')
        image_creator = ImageCreate(results)
        charts_results = asyncio.run(image_creator.run())
        logger.info(f'✅ 图表绘制完成.....')

        # 生成每个维度分析结论
        logger.info("正在生成每个维度分析结论.....")
        dimension_conclusion = asyncio.run(get_dimension_conclusion(charts_results))
        logger.info(f'✅ 每个维度分析结论生成完成.....')

        # todo debug
        # dimension_conclusion = [{'analysis_name': '按省份划分的高校分布分析', 'result': {'markdown': '# 按省份划分的高校分布分析\n\n分析时间: 2025-06-06 17:14:59\n\n## 省份分布统计\n\n| 省份 | 学校 |\n| --- | --- |\n| 上海 | 65 |\n| 云南 | 82 |\n| 内蒙古 | 56 ...2 |\n| 福建 | 90 |\n| 西藏 | 6 |\n| 贵州 | 77 |\n| 辽宁 | 110 |\n| 重庆 | 73 |\n| 陕西 | 104 |\n| 青海 | 12 |\n| 香港 | 14 |\n| 黑龙江 | 81 |\n\n', 'results': {'analysis_id': 'school_distribution_by_province', 'analysis_name': '按省份划分的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 省份 | 学校 |\n| --- | --- |\n| 上海 | 65 |\n| 云南 | 82 |\n| 内蒙古 | 56 |\n| 北京 | 102 |\n| 吉林 | 70 |\n| 四川 | 137 |\n| 天津 | 62 |\n| 宁... | 52 |\n| 福建 | 90 |\n| 西藏 | 6 |\n| 贵州 | 77 |\n| 辽宁 | 110 |\n| 重庆 | 73 |\n| 陕西 | 104 |\n| 青海 | 12 |\n| 香港 | 14 |\n| 黑龙江 | 81 |', 'name': '省份分布统计'}], 'time_series': None, 'timestamp': '2025-06-06 17:14:59'}, 'status': 'success'}, 'save_path': 'D:\\project\\研究\\data_analysic_agent\\save_chart\\按省份划分的高校分布分析.png', 'status': 'success', 'title': '按省份划分的高校分布分析', 'txt': ''}, {'analysis_name': '按办学类型划分的高校分布分析', 'result': {'markdown': '# 按办学类型划分的高校分布分析\n\n分析时间: 2025-06-06 17:14:59\n\n## 办学类型分布\n\n| 办学类型 | 学校 |\n| --- | --- |\n| 中外合作办学 | 20 |\n| 公办 | 2072 |\n| 民办 | 764 |\n\n', 'results': {'analysis_id': 'school_type_distribution', 'analysis_name': '按办学类型划分的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 办学类型 | 学校 |\n| --- | --- |\n| 中外合作办学 | 20 |\n| 公办 | 2072 |\n| 民办 | 764 |', 'name': '办学类型分布'}], 'time_series': None, 'timestamp': '2025-06-06 17:14:59'}, 'status': 'success'}, 'save_path': 'D:\\project\\研究\\data_analysic_agent\\save_chart\\按办学类型划分的高校分布分析.png', 'status': 'success', 'title': '按办学类型划分的高校分布分析', 'txt': ''}, {'analysis_name': '高校层次与类别组合分析', 'result': {'markdown': '# 高校层次与类别组合分析\n\n分析时间: 2025-06-06 17:15:00\n\n## 水平层次与办学类别组合\n\n| 水平层次 | 办学类别 |\n| --- | --- |\n| 专科（高职） | 1499 |\n| 普通本科 | 1357 |\n\n', 'results': {'analysis_id': 'school_level_and_category', 'analysis_name': '高校层次与类别组合分析', 'correlation': None, 'dimensions': [{'markdown': '| 水平层次 | 办学类别 |\n| --- | --- |\n| 专科（高职） | 1499 |\n| 普通本科 | 1357 |', 'name': '水平层次与办学类别组合'}], 'time_series': None, 'timestamp': '2025-06-06 17:15:00'}, 'status': 'success'}, 'save_path': 'D:\\project\\研究\\data_analysic_agent\\save_chart\\高校层次与类别组合分析.png', 'status': 'success', 'title': '高校层次与类别组合分析', 'txt': '\n在本次《<span style="font-weight: bold;">高校层次与类别组合分析</span>》中，我们对不同水平层次的高校及其对应的办学类别数量进行了统计分析。以下是主要发现：\n\n1. <span style="color:...lor: #4169E1;">47.9%</span>，两者基本持平，显示出我国高等教育结构的多样性。\n\n综上所述，我国高校在办学类别上的布局呈现出较为均衡的发展态势，其中专科（高职）类高校在数量上稍占优势，但普通本科类高校同样具备显著影响力。\n'}, {'analysis_name': '省份-城市维度下的高校分布分析', 'result': {'markdown': '# 省份-城市维度下的高校分布分析\n\n分析时间: 2025-06-06 17:15:00\n\n## 省份与城市组合分布\n\n| 省份 | 城市 | 学校 |\n| --- | --- | --- |\n| 上海 | 1 | 65 |\n| 云... 贵州 | 9 | 77 |\n| 辽宁 | 14 | 110 |\n| 重庆 | 1 | 73 |\n| 陕西 | 10 | 104 |\n| 青海 | 3 | 12 |\n| 香港 | 3 | 14 |\n| 黑龙江 | 13 | 81 |\n\n', 'results': {'analysis_id': 'province_city_school_distribution', 'analysis_name': '省份-城市维度下的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 省份 | 城市 | 学校 |\n| --- | --- | --- |\n| 上海 | 1 | 65 |\n| 云南 | 14 | 82 |\n| 内蒙古 | 12 | 56 |\n| 北京 | 1 | 102 |\n| 吉林 | 9 | 70 ...|\n| 贵州 | 9 | 77 |\n| 辽宁 | 14 | 110 |\n| 重庆 | 1 | 73 |\n| 陕西 | 10 | 104 |\n| 青海 | 3 | 12 |\n| 香港 | 3 | 14 |\n| 黑龙江 | 13 | 81 |', 'name': '省份与城市组合分布'}], 'time_series': None, 'timestamp': '2025-06-06 17:15:00'}, 'status': 'success'}, 'save_path': 'D:\\project\\研究\\data_analysic_agent\\save_chart\\省份-城市维度下的高校分布分析.png', 'status': 'success', 'title': '省份-城市维度下的高校分布分析', 'txt': ''}]
        dimension_conclusion = [{'analysis_name': '按省份划分的高校分布分析', 'result': {'markdown': '# 按省份划分的高校分布分析\n\n分析时间: 2025-06-06 17:14:59\n\n## 省份分布统计\n\n| 省份 | 学校 |\n| --- | --- |\n| 上海 | 65 |\n| 云南 | 82 |\n| 内蒙古 | 56 ...2 |\n| 福建 | 90 |\n| 西藏 | 6 |\n| 贵州 | 77 |\n| 辽宁 | 110 |\n| 重庆 | 73 |\n| 陕西 | 104 |\n| 青海 | 12 |\n| 香港 | 14 |\n| 黑龙江 | 81 |\n\n', 'results': {'analysis_id': 'school_distribution_by_province', 'analysis_name': '按省份划分的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 省份 | 学校 |\n| --- | --- |\n| 上海 | 65 |\n| 云南 | 82 |\n| 内蒙古 | 56 |\n| 北京 | 102 |\n| 吉林 | 70 |\n| 四川 | 137 |\n| 天津 | 62 |\n| 宁... | 52 |\n| 福建 | 90 |\n| 西藏 | 6 |\n| 贵州 | 77 |\n| 辽宁 | 110 |\n| 重庆 | 73 |\n| 陕西 | 104 |\n| 青海 | 12 |\n| 香港 | 14 |\n| 黑龙江 | 81 |', 'name': '省份分布统计'}], 'time_series': None, 'timestamp': '2025-06-06 17:14:59'}, 'status': 'success'}, 'save_path': 'E:\\data_analysic_agent\\save_chart\\按省份划分的高校分布分析.png', 'status': 'success', 'title': '按省份划分的高校分布分析', 'txt': ''}, {'analysis_name': '按办学类型划分的高校分布分析', 'result': {'markdown': '# 按办学类型划分的高校分布分析\n\n分析时间: 2025-06-06 17:14:59\n\n## 办学类型分布\n\n| 办学类型 | 学校 |\n| --- | --- |\n| 中外合作办学 | 20 |\n| 公办 | 2072 |\n| 民办 | 764 |\n\n', 'results': {'analysis_id': 'school_type_distribution', 'analysis_name': '按办学类型划分的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 办学类型 | 学校 |\n| --- | --- |\n| 中外合作办学 | 20 |\n| 公办 | 2072 |\n| 民办 | 764 |', 'name': '办学类型分布'}], 'time_series': None, 'timestamp': '2025-06-06 17:14:59'}, 'status': 'success'}, 'save_path': 'E:\\data_analysic_agent\\save_chart\\按办学类型划分的高校分布分析.png', 'status': 'success', 'title': '按办学类型划分的高校分布分析', 'txt': ''}, {'analysis_name': '高校层次与类别组合分析', 'result': {'markdown': '# 高校层次与类别组合分析\n\n分析时间: 2025-06-06 17:15:00\n\n## 水平层次与办学类别组合\n\n| 水平层次 | 办学类别 |\n| --- | --- |\n| 专科（高职） | 1499 |\n| 普通本科 | 1357 |\n\n', 'results': {'analysis_id': 'school_level_and_category', 'analysis_name': '高校层次与类别组合分析', 'correlation': None, 'dimensions': [{'markdown': '| 水平层次 | 办学类别 |\n| --- | --- |\n| 专科（高职） | 1499 |\n| 普通本科 | 1357 |', 'name': '水平层次与办学类别组合'}], 'time_series': None, 'timestamp': '2025-06-06 17:15:00'}, 'status': 'success'}, 'save_path': 'E:\\data_analysic_agent\\save_chart\\高校层次与类别组合分析.png', 'status': 'success', 'title': '高校层次与类别组合分析', 'txt': '\n在本次《<span style="font-weight: bold;">高校层次与类别组合分析</span>》中，我们对不同水平层次的高校及其对应的办学类别数量进行了统计分析。以下是主要发现：\n\n1. <span style="color:...lor: #4169E1;">47.9%</span>，两者基本持平，显示出我国高等教育结构的多样性。\n\n综上所述，我国高校在办学类别上的布局呈现出较为均衡的发展态势，其中专科（高职）类高校在数量上稍占优势，但普通本科类高校同样具备显著影响力。\n'}, {'analysis_name': '省份-城市维度下的高校分布分析', 'result': {'markdown': '# 省份-城市维度下的高校分布分析\n\n分析时间: 2025-06-06 17:15:00\n\n## 省份与城市组合分布\n\n| 省份 | 城市 | 学校 |\n| --- | --- | --- |\n| 上海 | 1 | 65 |\n| 云... 贵州 | 9 | 77 |\n| 辽宁 | 14 | 110 |\n| 重庆 | 1 | 73 |\n| 陕西 | 10 | 104 |\n| 青海 | 3 | 12 |\n| 香港 | 3 | 14 |\n| 黑龙江 | 13 | 81 |\n\n', 'results': {'analysis_id': 'province_city_school_distribution', 'analysis_name': '省份-城市维度下的高校分布分析', 'correlation': None, 'dimensions': [{'markdown': '| 省份 | 城市 | 学校 |\n| --- | --- | --- |\n| 上海 | 1 | 65 |\n| 云南 | 14 | 82 |\n| 内蒙古 | 12 | 56 |\n| 北京 | 1 | 102 |\n| 吉林 | 9 | 70 ...|\n| 贵州 | 9 | 77 |\n| 辽宁 | 14 | 110 |\n| 重庆 | 1 | 73 |\n| 陕西 | 10 | 104 |\n| 青海 | 3 | 12 |\n| 香港 | 3 | 14 |\n| 黑龙江 | 13 | 81 |', 'name': '省份与城市组合分布'}], 'time_series': None, 'timestamp': '2025-06-06 17:15:00'}, 'status': 'success'}, 'save_path': 'E:\\data_analysic_agent\\save_chart\\省份-城市维度下的高校分布分析.png', 'status': 'success', 'title': '省份-城市维度下的高校分布分析', 'txt': ''}]

        # 生成报告
        logger.info("正在生成数据分析报告.....")
        GenerateReport(dimension_conclusion).run()
        logger.info(f'✅ 数据分析报告生成完成.....')


def general_analysis_dimension(markdown_output, query):
    logger.info("正在生成数据分析维度.....")
    prompt = analysis_dimension_prompt.format(df=markdown_output, query=query)
    content = modelscope_api(prompt)
    profiles_list = parse_profiles_data_safe(content)
    return profiles_list


def parse_profiles_data_safe(data):
    logger.info("正在解析分析维度....")
    pattern = r"profiles\d+ = ({.*?})\n\n"
    profiles_list = []

    for match in re.finditer(pattern, data, re.DOTALL):
        try:
            # 使用更安全的字面量求值函数
            profile_dict = ast.literal_eval(match.group(1))
            profiles_list.append(profile_dict)
        except (SyntaxError, ValueError) as e:
            logger(f"分析维度解析错误: {e}\n在字符串中: {match.group(1)}")

    return profiles_list


def parse_conclusion(res):
    logger.info("正在解析数据分析结论....")
    title = re.findall(r'title = "(.*?)"', res)
    txt = re.findall(r'txt = """(.*?)"""', res, re.S)

    title = title[0] if title else ""
    txt = txt[0] if txt else ""
    return title, txt


def analysis_dimension(config_json, data):
    """
    分析维度的主函数
        Args:
            excel_url: Excel文件URL
            config_json: 配置JSON字符串
            logger: 日志记录器
        Returns:
            分析结果字典，包含Markdown表格
    """
    try:
        analyzer = DataAnalyzer(str(config_json), data)
        results = analyzer.run_analysis()

        # 构建完整的Markdown输出
        markdown_output = f"# {results['analysis_name']}\n\n"
        markdown_output += f"分析时间: {results['timestamp']}\n\n"

        # 添加维度分析结果
        for dim_result in results['dimensions']:
            markdown_output += f"## {dim_result['name']}\n\n"
            markdown_output += dim_result.get('markdown',
                                              f"**分析失败: {dim_result.get('error', '未知错误')}**") + "\n\n"

        # 添加时间序列分析结果
        if results['time_series']:
            markdown_output += f"## {results['time_series']['name']}\n\n"
            markdown_output += results['time_series'].get('markdown',
                                                          f"**分析失败: {results['time_series'].get('error', '未知错误')}**") + "\n\n"

        # 添加相关性分析结果
        if results['correlation']:
            markdown_output += f"## {results['correlation']['name']}\n\n"
            markdown_output += results['correlation'].get('markdown',
                                                          f"**分析失败: {results['correlation'].get('error', '未知错误')}**") + "\n\n"

        return {
            "status": "success",
            "markdown": markdown_output,
            "results": results
        }

    except Exception as e:
        import traceback
        error_msg = f"分析失败: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "markdown": f"**{error_msg}**",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def get_dimension_conclusion(charts_results):
    async def run_task(result):
        prompt = analysis_conclusion_prompt.format(outmarkdown=result['result']['markdown'])
        res = modelscope_api(prompt)
        title, txt = parse_conclusion(res)
        if not title or not title:
            logger.warning(f"维度：{result['analysis_name']} title or txt 解析错误，为空了")
        result['title'] = title
        result['txt'] = txt
        return result

    # 创建多个异步任务
    tasks = [run_task(result) for result in charts_results]

    # 并发执行所有任务
    results = await asyncio.gather(*tasks)

    return results
