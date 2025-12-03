import os
import subprocess
import time
import sys

# 后端目录路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), 'backend')
# 后端服务地址
BACKEND_URL = 'http://localhost:8000'


def start_backend():
    """启动后端服务"""
    # 切换到后端目录
    os.chdir(BACKEND_DIR)

    print("正在启动后端服务...")
    print("请稍候，服务正在初始化...")

    # 检查并安装依赖
    print("\n检查并安装依赖...")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        shell=True,
        check=True,
    )

    # 启动uvicorn服务器
    process = subprocess.Popen(
        [
            sys.executable,
            '-c',
            'import subprocess; subprocess.run(["uvicorn", "main:app", "--reload"])',
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 等待服务启动
    time.sleep(3)  # 等待3秒，给服务足够的启动时间

    print(f"\n后端服务已启动！")
    print("========================================")
    print(f"服务地址: {BACKEND_URL}")
    print(f"API文档: {BACKEND_URL}/docs")
    print(f"API红文档: {BACKEND_URL}/redoc")
    print("按 Ctrl+C 停止服务")
    print("========================================")

    try:
        # 保持脚本运行
        process.wait()
    except KeyboardInterrupt:
        print("\n正在停止后端服务...")
        process.terminate()
        print("后端服务已停止")


if __name__ == "__main__":
    start_backend()
