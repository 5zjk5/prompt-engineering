"""
API Agent - LLM API 代理桌面端
双击启动，关闭窗口即停止所有代理
"""
import sys
import os
import logging
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api_agent")

HOST = "127.0.0.1"
PORT = 12345


def start_server():
    """在后台线程启动 FastAPI 服务器"""
    import uvicorn
    from server import app
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
    )


def main():
    import webview

    # 先启动 FastAPI 服务器（后台线程）
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    import time
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/", timeout=1)
            break
        except Exception:
            time.sleep(0.2)

    logger.info(f"API Agent 已启动: http://{HOST}:{PORT}")

    # 创建桌面窗口
    window = webview.create_window(
        title="API Agent - LLM 代理管理",
        url=f"http://{HOST}:{PORT}",
        width=960,
        height=720,
        resizable=True,
        min_size=(640, 480),
    )

    # 启动 webview（阻塞，关闭窗口后退出）
    webview.start(debug=False)

    logger.info("API Agent 已停止，所有代理接口已关闭")
    sys.exit(0)


if __name__ == "__main__":
    main()
