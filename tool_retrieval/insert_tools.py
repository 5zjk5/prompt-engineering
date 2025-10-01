import json
import os
import time
import requests
from typing import List, Dict, Any

def insert_single_tool(tool: Dict[str, Any], base_url: str):
    """
    使用requests插入单个工具
    
    Args:
        tool: 工具数据
        base_url: API基础URL
        
    Returns:
        包含成功状态和响应信息的字典
    """
    tool_name = tool.get('name', '未知工具')
    
    try:
        response = requests.post(
            f"{base_url}/tools/insert_tool",
            json={"tool_json": tool, "tool_optimized": False},
            timeout=30
        )
        
        response_text = response.text
        
        if response.status_code == 200:
            return {
                'success': True,
                'status_code': response.status_code,
                'response_text': response_text
            }
        else:
            return {
                'success': False,
                'status_code': response.status_code,
                'response_text': response_text
            }
            
    except Exception as e:
        # 捕获并返回异常信息
        return {
            'success': False,
            'status_code': None,
            'response_text': str(e)
        }

def insert_tools_from_json():
    """
    从tool.json文件中读取工具并串行入库
    """
    # 定义文件路径
    data_dir = "data"
    tool_json_path = os.path.join(data_dir, "tool.json")
    
    # API基础URL - 默认本地服务
    base_url = "http://localhost:8009"
    
    # 存储所有工具名称的列表
    all_tools_list = []
    
    # 存储失败工具名称的列表
    failed_tools_list = []
    
    # 读取tool.json文件
    print(f"正在读取工具文件: {tool_json_path}")
    with open(tool_json_path, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    # 收集所有工具名称
    for tool in tools:
        tool_name = tool.get('name', '未知工具')
        all_tools_list.append(tool_name)
    
    print(f"成功读取工具文件，共{len(tools)}个工具")
    print("开始串行插入工具...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 初始化统计信息
    total_tools = len(tools)
    total_success = 0
    total_failed = 0
    all_errors = []
    
    try:
        # 串行处理每个工具
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('name', '未知工具')
            print(f"\n处理工具 {i}/{total_tools}: {tool_name}")
            
            # 插入单个工具
            result = insert_single_tool(tool, base_url)
            
            if result['success']:
                # 处理成功
                total_success += 1
                print(f"  ✓ 成功插入工具: {tool_name}")
            else:
                # 处理失败
                total_failed += 1
                if result['status_code']:
                    error_msg = f"插入工具失败: {tool_name}, 状态码: {result['status_code']}, 响应: {result['response_text']}"
                else:
                    error_msg = f"插入工具失败: {tool_name}, 错误: {result['response_text']}"
                
                all_errors.append(error_msg)
                failed_tools_list.append(tool_name)
                print(f"  ✗ {error_msg}")
        
        # 计算总耗时
        elapsed_time = time.time() - start_time
        
        # 计算成功的工具列表
        success_tools_list = [tool for tool in all_tools_list if tool not in failed_tools_list]
        
        # 打印汇总结果
        print(f"\n工具入库完成!")
        print(f"总工具数: {total_tools}")
        print(f"成功入库数: {total_success}")
        print(f"失败数: {total_failed}")
        print(f"成功率: {total_success/total_tools*100:.2f}%")
        print(f"总耗时: {elapsed_time:.2f}秒")
        print(f"平均每工具耗时: {elapsed_time/total_tools:.2f}秒")
        
        # 打印所有工具列表
        print(f"\n所有工具列表 (共{len(all_tools_list)}个):")
        for i, tool_name in enumerate(all_tools_list, 1):
            print(f"  {i}. {tool_name}")
        
        # 打印成功插入的工具列表
        print(f"\n成功插入的工具 (共{len(success_tools_list)}个):")
        for i, tool_name in enumerate(success_tools_list, 1):
            print(f"  {i}. {tool_name}")
        
        # 打印失败的工具列表
        if failed_tools_list:
            print(f"\n插入失败的工具 (共{len(failed_tools_list)}个):")
            for i, tool_name in enumerate(failed_tools_list, 1):
                print(f"  {i}. {tool_name}")
        
        # 如果有错误，打印详细错误信息
        if all_errors:
            print(f"\n详细错误信息 (共{len(all_errors)}个错误):")
            for i, error in enumerate(all_errors, 1):
                print(f"  {i}. {error}")
        
    except Exception as e:
        print(f"工具入库过程中出错: {e}")
        # 打印失败的工具列表
        if failed_tools_list:
            print(f"\n插入失败的工具 (共{len(failed_tools_list)}个):")
            for i, tool_name in enumerate(failed_tools_list, 1):
                print(f"  {i}. {tool_name}")
        
        # 如果有错误，打印详细错误信息
        if all_errors:
            print(f"\n详细错误信息 (共{len(all_errors)}个错误):")
            for i, error in enumerate(all_errors, 1):
                print(f"  {i}. {error}")

if __name__ == "__main__":
    # 运行函数
    insert_tools_from_json()
