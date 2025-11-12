import pandas as pd
import json
import os
import sys
import time
from fastapi.testclient import TestClient

# 导入FastAPI应用
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from svs_service import app

# 创建测试客户端
client = TestClient(app)

def evaluate_retrieval():
    """
    评估工具检索准确率的脚本
    """
    # 定义文件路径
    data_dir = "data"
    input_excel_path = os.path.join(data_dir, "query.xlsx")
    output_excel_path = "eval_retrieval.xlsx"
    method = "hybrid"
    n_results = 10
    
    try:
        # 读取Excel文件
        print(f"正在读取Excel文件: {input_excel_path}")
        df = pd.read_excel(input_excel_path)
        # df = df.head(2)
        print(f"成功读取Excel文件，共{len(df)}行数据")
        print(f"列名: {df.columns.tolist()}")
        
        # 检查必要的列是否存在
        if 'query' not in df.columns:
            print("错误: Excel文件中缺少'query'列")
            return
        
        # 如果没有tool列，创建一个空列用于存储标准答案
        if 'tool' not in df.columns:
            df['tool'] = ""
            print("警告: Excel文件中缺少'tool'列，已创建空列")
        
        # 创建新列用于存储检索结果和评估结果
        df['retrieval_res'] = ""
        df['flag'] = ""
        df['retrieval_time'] = ""
        
        # 逐行处理查询
        total_rows = len(df)
        for index, row in df.iterrows():
            query = row['query']
            tool = row['tool'] if 'tool' in row else ""
            
            print(f"处理第{index+1}/{total_rows}行: {query[:50]}...")
            print(f'标准答案: {tool}')
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 使用混合检索方法获取结果
                response = client.post(
                    "/tools/retrieval_tool",
                    json={"query": query, "method": method, "n_results": n_results}
                )
                
                # 记录结束时间并计算耗时
                end_time = time.time()
                retrieval_time = end_time - start_time
                
                if response.status_code != 200:
                    print(f"  检索请求失败，状态码: {response.status_code}")
                    print(f"  响应内容: {response.text}")
                    df.at[index, 'retrieval_res'] = f"错误: 状态码 {response.status_code}"
                    df.at[index, 'flag'] = 0
                    df.at[index, 'retrieval_time'] = retrieval_time
                    continue
                
                # 解析响应
                response_data = response.json()
                results = response_data.get('results', [])
                
                # 提取检索到的工具名称
                retrieved_tools = []
                for result in results:
                    retrieved_tools.append(result.get('tool_id', ''))
                
                # 将检索结果存储为JSON字符串
                df.at[index, 'retrieval_res'] = json.dumps(retrieved_tools, ensure_ascii=False)
                
                # 评估检索结果是否正确
                flag = 0
                if tool and retrieved_tools:
                    # 如果标准答案在检索结果中，则标记为正确
                    flag = 1 if tool in retrieved_tools else 0
                
                df.at[index, 'flag'] = flag
                df.at[index, 'retrieval_time'] = retrieval_time
                print(f"  检索结果: {retrieved_tools[:3]}...")  # 只显示前3个结果
                print(f"  标准答案: {tool}")
                print(f"  是否正确: {flag}")
                print(f"  检索耗时: {retrieval_time:.4f}秒")
                
            except Exception as e:
                print(f"  处理查询时出错: {e}")
                df.at[index, 'retrieval_res'] = f"错误: {str(e)}"
                df.at[index, 'flag'] = 0
                df.at[index, 'retrieval_time'] = 0
            
            print('\n')
        
        # 计算准确率
        if 'flag' in df.columns:
            correct_count = df['flag'].sum()
            total_count = len(df)
            accuracy = correct_count / total_count if total_count > 0 else 0
            print(f"\n评估完成!")
            print(f"总查询数: {total_count}")
            print(f"正确数: {correct_count}")
            print(f"准确率: {accuracy:.2%}")
        
        # 保存结果到新的Excel文件
        df.to_excel(output_excel_path, index=False)
        print(f"\n结果已保存到: {output_excel_path}")
        
    except Exception as e:
        print(f"评估过程中出错: {e}")

if __name__ == "__main__":
    evaluate_retrieval()
