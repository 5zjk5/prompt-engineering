import logging
import sys
import re
from pathlib import Path
from datetime import datetime


def define_log_level(project_root, topic, print_level="INFO", logfile_level="DEBUG"):
    """
    创建独立的 logger，支持记录模块、函数、行号
    """
    topic = re.sub(r'[\/\\:\*\?"<>\|]', '_', topic)

    logger = logging.getLogger(topic)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    log_name = f"{topic[:30]}_{now.strftime('%H_%M_%S')}.log"
    log_dir = Path(project_root) / "logs" / date_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志格式包含模块、函数、行号等信息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(print_level)
    console_handler.setFormatter(formatter)

    # 文件 handler
    file_handler = logging.FileHandler(log_dir / log_name, encoding='utf-8')
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 日志路径
    log_path = log_dir / log_name
    logger.info(f"日志路径: {log_path}")

    return logger


if __name__ == "__main__":
    logger = define_log_level(r'C:\Users\zhoujk2\Desktop\test\langchain-langgraph-V1.0\案例\Deep_Research', 'test')
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        