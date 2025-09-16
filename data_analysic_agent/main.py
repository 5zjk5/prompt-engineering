from logs.logger import logger
from workflow.data_explore import DataExplore


if __name__ == '__main__':
    """
    1、数据解读，数据探索，输入分析建议，进行探索分析数据，适用于一张表的数据，并把结果保存为 markdown
    2、数据问答，用户输入问题，根据用户问题进行解答
    """
    intent = '1'

    data_path = r'D:\project\研究\data_analysic_agent\data\大学专业\school.csv'
    data_path = r'E:\data_analysic_agent\data\大学专业\school.csv'

    if intent == '1':
        logger.info('正在进行了数据探索....')
        query = '' #input('请输入你的分析建议：')
        DataExplore(data_path, query).run()
    else:
        logger.info('数据问答，用户输入问题，执行规划，一个一个完成用户问题')
