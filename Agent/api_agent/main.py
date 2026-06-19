"""
API Agent - LLM API 代理桌面端
双击启动，关闭窗口即停止所有代理
"""
import sys
import os
import logging
import threading

HOST = "127.0.0.1"
PORT = 12345


def _get_app_dir() -> str:
    """日志文件目录：exe旁边 或 源码目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _setup_logging():
    """配置日志：写入文件，每次启动覆盖"""
    log_file = os.path.join(_get_app_dir(), "api_agent.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        filename=log_file,
        filemode="w",  # 每次启动覆盖
        encoding="utf-8",
    )


logger = logging.getLogger("api_agent")


def start_server():
    """在后台线程启动 FastAPI 服务器"""
    import uvicorn
    from server import app
    logger.info(f"正在启动 FastAPI 服务器于 http://{HOST}:{PORT}")
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
    )


def main():
    _setup_logging()

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
