import logging
import sys
import re
from pathlib import Path
from datetime import datetime


def define_log_level(project_root, mode, print_level="INFO", logfile_level="DEBUG"):
    """
    创建独立的 logger，支持记录模块、函数、行号
    
    Args:
        project_root: 项目根目录路径
        mode: 日志模式，如 'insert', 'select', 'update', 'delete' 等
        print_level: 控制台打印级别，默认为 "INFO"
        logfile_level: 日志文件记录级别，默认为 "DEBUG"
    """
    # 清理模式名称，确保文件名安全
    mode = re.sub(r'[\/\\:\*\?"<>\|]', '_', mode)
    
    # 根据模式确定日志文件名，包含今天的日期
    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    log_name = f"{mode}_{now.strftime('%Y-%m-%d')}.log"
    
    # 检查是否已经存在该logger
    logger = logging.getLogger(mode)
    
    # 如果logger已经存在且有处理器，先清除所有处理器
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

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

    # 文件 handler，使用追加模式
    file_handler = logging.FileHandler(log_dir / log_name, encoding='utf-8', mode='a')
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# 示例用法
if __name__ == "__main__":
    # 使用insert模式创建logger
    logger, log_name = define_log_level(r'D:\project\deep_search\svs_deepsearch', 'insert')
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    
    print(f"日志文件名: {log_name}")
    
    # 使用select模式创建logger
    select_logger, select_log_name = define_log_level(r'D:\project\deep_search\svs_deepsearch', 'select')
    select_logger.info("This is a select operation log")
    print(f"选择模式日志文件名: {select_log_name}")
