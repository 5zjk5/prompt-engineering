"""会话级日志工具 — 每个会话独立文件，生产级结构化日志

日志路径：logs/user/{chat_mode}/{conv_uid}.log
日志格式：2026-06-14 10:30:00.123 | INFO | upload.py:42 | upload_file() | 消息内容

使用方式：
    logger = get_session_logger(conv_uid, "chat_excel")
    logger.info("用户输入: %s", user_input)
    logger.warning("xx失败: %s", err_msg)
"""

import logging
import os
import sys

from app.core import config

# 保存已创建的 logger，避免重复添加 handler
_logger_cache: dict = {}


def _make_log_dir(chat_mode: str) -> str:
    """创建并返回日志目录 logs/user/{chat_mode}/"""
    log_dir = os.path.join(config.LOG_DIR, "user", chat_mode)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_session_logger(conv_uid: str, chat_mode: str = "chat_excel") -> logging.Logger:
    """获取会话级别的日志记录器

    Args:
        conv_uid: 会话唯一 ID
        chat_mode: 会话模式（chat_excel / react_agent）

    Returns:
        配置好的 Logger 实例
    """
    cache_key = f"{chat_mode}.{conv_uid}"
    if cache_key in _logger_cache:
        return _logger_cache[cache_key]

    logger = logging.getLogger(cache_key)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 避免日志重复传到根 logger

    # 文件 Handler — 一个会话一个日志文件
    log_dir = _make_log_dir(chat_mode)
    log_path = os.path.join(log_dir, f"{conv_uid}.log")
    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
        mode="a",
    )
    file_handler.setLevel(logging.DEBUG)

    # 控制台 Handler — 开发调试用
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 统一日志格式
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d | %(levelname)-5s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_cache[cache_key] = logger
    return logger


def close_session_logger(conv_uid: str, chat_mode: str = "chat_excel"):
    """关闭会话日志记录器，清理 handler 和缓存"""
    cache_key = f"{chat_mode}.{conv_uid}"
    logger = _logger_cache.pop(cache_key, None)
    if logger:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
