import os
import subprocess
import time
import webbrowser
import sys

# 前端目录路径
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')
# 前端服务地址
FRONTEND_URL = 'http://localhost:5173'


def start_frontend():
    """启动前端服务"""
    # 切换到前端目录
    os.chdir(FRONTEND_DIR)
    
    print("正在启动前端服务...")
    print("请稍候，服务正在初始化...")
    
    # 启动npm run dev命令
    process = subprocess.Popen(
        [sys.executable, '-c', 'import subprocess; subprocess.run(["npm", "run", "dev"])'],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务启动
    time.sleep(3)  # 等待3秒，给服务足够的启动时间
    
    # 自动打开浏览器
    print(f"前端服务已启动，正在打开浏览器访问: {FRONTEND_URL}")
    webbrowser.open(FRONTEND_URL)
    
    print("\n前端服务启动成功！")
    print("========================================")
    print(f"服务地址: {FRONTEND_URL}")
    print("按 Ctrl+C 停止服务")
    print("========================================")
    
    try:
        # 保持脚本运行
        process.wait()
    except KeyboardInterrupt:
        print("\n正在停止前端服务...")
        process.terminate()
        print("前端服务已停止")


if __name__ == "__main__":
    start_frontend()
    