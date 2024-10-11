# coding:utf8
import sqlite3
import threading
import queue
from sqlalchemy import create_engine, inspect


# 设置数据库连接
db_path = 'data/dataset/博金杯比赛数据.db'
engine = create_engine(f'sqlite:///{db_path}')


def execute_sql_with_timeout(sql, db_path, result_queue, timeout):
    """执行 SQL 并将结果放入队列"""
    print(f'执行 sql：\n{sql}')
    conn = sqlite3.connect(db_path, timeout=timeout)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        result_queue.put(results)
    except Exception as e:
        result_queue.put(e)
    finally:
        conn.close()


def execute_sql(sql, print):
    """执行 SQL 并设置超时"""
    timeout = 120
    result_queue = queue.Queue()
    thread = threading.Thread(target=execute_sql_with_timeout, args=(sql, db_path, result_queue, timeout))
    thread.start()

    thread.join(timeout=timeout)

    if thread.is_alive():
        print("执行超时，强制停止")
        # 注意：SQLite 没有提供直接的取消执行的方法，所以这里只能等待线程结束
        thread.join()  # 等待线程结束（尽管这可能会导致长时间等待）
        return None  # 或者返回一个特定的超时标志
    else:
        result = result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result


def inspect_db_structure():
    """获得所有表结构，包括列名和列的数据类型"""
    inspector = inspect(engine)
    structure = {}

    # 获取所有表的名字
    for table_name in inspector.get_table_names():
        columns_info = []

        # 获取每个表的列信息
        for index, column in enumerate(inspector.get_columns(table_name)):
            # 每个列的信息可以包括但不限于：
            # 'name' - 列名
            # 'type' - 列的数据类型
            # 'nullable' - 是否允许为空
            # 'default' - 默认值
            # 'autoincrement' - 是否自动递增
            # 'comment' - 注释
            column_info = {
                f'column{index + 1}': column['name'],
                'type': str(column['type']),  # 将数据类型转换为字符串
            }
            columns_info.append(column_info)

        # 将列信息与表关联起来
        structure[table_name] = columns_info

    return structure


def process_field(sql):
    """
    处理生成 sql 的字段，模型能力问题，生成的字段对，但是有误差，在获得字段名是，带双引号的被自动去掉了
    智谱生成的少了 (元)
    通义能生成对，但少了双引号
    """
    field_dict = {
        '昨收盘(元)': '"昨收盘(元)"',
        '今开盘(元)': '"今开盘(元)"',
        '最高价(元)': '"最高价(元)"',
        '最低价(元)': '"最低价(元)"',
        '收盘价(元)': '"收盘价(元)"',
        '成交量(股)': '"成交量(股)"',
        '成交金额(元)': '"成交金额(元)"',
        '所属国家(地区)': '"所属国家(地区)"',
    }
    for key in field_dict.keys():
        if key in sql:
            sql = sql.replace(key, field_dict[key])
    sql = sql.replace('`', '').replace('""', '"')
    return sql
