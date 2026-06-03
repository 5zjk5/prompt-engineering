from fastapi.testclient import TestClient
from main import app
from dotenv import load_dotenv


load_dotenv()


client = TestClient(app)


def test_today_news():
    """测试 /api/today_news 接口"""
    response = client.get("/api/today_news")
    assert response.status_code == 200
    data = response.json()
    print(f"  响应数据: {data}")


if __name__ == "__main__":
    print("开始测试 FastAPI 接口...\n")
    test_today_news()
    print("\n所有测试完成！")
