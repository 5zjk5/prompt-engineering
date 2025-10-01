import json
import os
import sys
from fastapi.testclient import TestClient

# 导入FastAPI应用
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from svs_service import app

from dotenv import load_dotenv
load_dotenv()

#region test_data
test_data = """
[
    {
        "name": "test_tool_1",
        "description": "这是一个测试工具1",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "参数1111的描述"
                }
            },
            "required": [
                "param1"
            ]
        }
    },
    {
        "name": "test_tool_1",
        "description": "这是一个update测试工具2222222222222222222222222222222",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "参数1的描述"
                },
                "param2": {
                    "type": "integer",
                    "description": "参数2的描述"
                }
            },
            "required": [
                "param1"
            ]
        }
    }
]
"""
#endregion

# 创建测试客户端
client = TestClient(app)
test_tools = json.loads(test_data)

def test_insert_tool():
    """测试插入工具API"""
    print("\n=== 测试插入工具API ===")
    tool = test_tools[0]
    response = client.post("/tools/insert_tool", json={"tool_json": tool, 'tool_optimized': False})
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")

def test_delete_tool():
    """测试删除工具API"""
    print("\n=== 测试删除工具API ===")
    tool_name = test_tools[0]["name"]
    response = client.post("/tools/delete_tool", json={"tool_name": tool_name})
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")

def test_update_tool():
    """测试更新工具API"""
    print("\n=== 测试更新工具API ===")
    updated_tool = test_tools[1]
    response = client.post("/tools/update_tool", json={"tool_json": updated_tool})
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")

def test_select_tool():
    """测试查询工具API"""
    print("\n=== 测试查询工具API ===")
    # 查询所有工具
    response = client.post("/tools/select_tool", json={})
    print(f"查询所有工具 - 状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    # 查询特定工具
    # tool_name = test_tools[0]["name"]
    # response = client.post("/tools/select_tool", json={"tool_name": tool_name})
    # print(f"查询工具 {tool_name} - 状态码: {response.status_code}")
    # print(f"响应内容: {response.text}")

def test_retrieval_tool():
    """测试检索工具API"""
    print("\n=== 测试检索工具API ===")
    query = "测试"
    response = client.post("/tools/retrieval_tool", json={"query": query, 'method': 'hybrid', 'n_results': 5})
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")


if __name__ == "__main__":
    print("开始执行API测试")

    # test_insert_tool()
    # test_select_tool()

    # test_update_tool()
    # test_select_tool()  # 更新后再次查询

    # test_delete_tool()
    # test_select_tool()  # 删除后再次查询

    test_retrieval_tool()
    # test_retrieval_tool()

    print("\n所有测试执行完毕")
