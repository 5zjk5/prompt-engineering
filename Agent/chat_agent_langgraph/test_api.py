import requests
import json
import time
from datetime import datetime


# API基础URL
BASE_URL = "http://localhost:8000"


def test_create_user():
    """测试create_user接口"""
    print("\n" + "="*50)
    print(f"测试create_user接口")
    print("="*50)
    try:
        # 发送GET请求到create_user接口
        response = requests.get(f"{BASE_URL}/create_user")
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ 测试失败: 发生异常 - {str(e)}")


def main():
    """主函数，运行所有测试"""
    print("API接口测试工具")
    print(f"测试目标: {BASE_URL}")
    
    # 测试create_user接口
    test_create_user()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)


if __name__ == "__main__":
    main()
    