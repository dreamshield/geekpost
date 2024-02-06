# coding=utf-8
import os.path
from datetime import datetime

from loguru import logger

APP_LOG_PATH = "./logs"
APP_LOG_NAME_PATTERN = "geek-post-{}.log"

APP_LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss:SSS} {level} From {thread.name} {module}.{function}: {line} : {message}"


def build_log_name():
    if not os.path.exists(APP_LOG_PATH):
        os.makedirs(APP_LOG_PATH)
    log_name = APP_LOG_NAME_PATTERN.format(datetime.now().strftime('%Y%m%d'))
    return APP_LOG_PATH + "/" + log_name


def log_config():
    logger.remove(handler_id=None)
    log_name = build_log_name()
    logger.add(log_name, format=APP_LOG_FORMAT, level="INFO", encoding="utf-8", enqueue=True, rotation="daily",
               retention="15 days")
