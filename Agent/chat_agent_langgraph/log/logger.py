import logging
import sys
import re
from pathlib import Path
from datetime import datetime


class OpenAIClientFilter(logging.Filter):
    """过滤器，用于过滤掉OpenAI客户端库的内部日志"""

    def filter(self, record):
        # 过滤掉来自_openai.py、_client.py和_base_client.py的日志
        if record.filename in ["_openai.py", "_client.py", "_base_client.py"]:
            return False
        return True


def service_log(service_log_path, print_level="INFO", logfile_level="DEBUG"):
    """
    创建独立的 logger，支持记录模块、函数、行号

    Args:
        service_log_path: 日志文件目录路径
        print_level: 控制台打印级别，默认为 "INFO"
        logfile_level: 日志文件记录级别，默认为 "DEBUG"
    """
    # 根据当前时间确定日志文件名（年月日时分秒）
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    log_name = f"{timestamp}.log"

    # 检查是否已经存在该logger
    logger = logging.getLogger()

    # 如果logger已经存在且有处理器，先清除所有处理器
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # 设置日志目录
    log_dir = Path(service_log_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志格式包含模块、函数、行号等信息
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"
    )

    # 创建过滤器实例
    openai_filter = OpenAIClientFilter()

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(print_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(openai_filter)

    # 文件 handler，使用追加模式
    file_handler = logging.FileHandler(log_dir / log_name, encoding="utf-8", mode="a")
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(openai_filter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
