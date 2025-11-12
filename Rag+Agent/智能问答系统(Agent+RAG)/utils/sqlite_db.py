# coding:utf8
import re
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy import inspect
from utils.prompts import glm4_generate_sql_prompt
from llm.llm_chain import base_llm_chain


# 设置数据库连接
db_path = 'data/dataset/博金杯比赛数据.db'
engine = create_engine(f'sqlite:///{db_path}')


def execute_sql(sql):
    """执行 sql"""
    # 处理字段
    sql = process_field(sql)
    # 匹配 sql
    sql = sql.replace('Observation:', '').replace('`', '').replace('sql', '').replace(':', '') \
            .replace('平均', '')

    conn = sqlite3.connect(db_path, timeout=180)
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    return results


def process_field(sql):
    """
    处理生成 sql 的字段，模型能力问题，生成的字段对，但是有误差，在获得字段名是，带双引号的被自动去掉了
    智谱生成的少了 (元)
    通义能生成对，但少了双引号
    """
    sql = sql.replace('(元)', '').replace('(股)', '').replace('(地区)', '').replace('报告期所属年度', '定期报告所属年度')
    field_dict = {
        '昨收盘': '"昨收盘(元)"',
        '今开盘': '"今开盘(元)"',
        '最高价': '"最高价(元)"',
        '最低价': '"最低价(元)"',
        '收盘价': '"收盘价(元)"',
        '成交量': '"成交量(股)"',
        '成交金额': '"成交金额(元)"',
        '所属国家': '"所属国家(地区)"',
    }
    for key in field_dict.keys():
        if key in sql:
            sql = sql.replace(key, field_dict[key])
    return sql


def inspect_db_structure():
    """获得所有表结构"""
    inspector = inspect(engine)
    structure = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        structure[table_name] = [column['name'] for column in columns]
    return structure


def generate_sql_by_question(question, llm):
    """根据问题生成 sql"""
    db_structure = inspect_db_structure()
    generate_sql = base_llm_chain(llm, glm4_generate_sql_prompt, question=question, db_structure=db_structure)
    generate_sql = re.findall('```sql(.*?)```', generate_sql, re.S)
    if generate_sql:
        return generate_sql[0]
    else:
        return None
