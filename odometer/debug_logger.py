# import standard libraries
from typing import List, Dict
import logging
from datetime import datetime as dt, timedelta
from pathlib import Path
import time


def create_logger(
    name: str = "test",
    level: str = "debug",
    base_folder: str = "log",
    prefix: str = "debug",
    ext: str = "log",
) -> logging.Logger:
    formatter = logging.Formatter(
        "%(relativeCreated)7d,%(asctime)s,[%(levelname)s], NAME:%(name)s, PID:%(processName)s, THR:%(threadName)s, MOD:%(module)s, MSG:%(message)s"
    )
    file_name = new_filename()
    file_handler = logging.FileHandler(file_name)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    if level == "info":
        logger.setLevel(logging.INFO)

    if level == "debug":
        logger.setLevel(logging.DEBUG)

    if level == "warning":
        logger.setLevel(logging.WARNING)
    logger.info("Start of log file")
    return logger


def new_filename(
    base_folder: str = "log", prefix: str = "debug", ext: str = "log"
) -> str:
    timestamp = dt.now().strftime("%Y-%m-%d_%H%M%S")
    Path(base_folder).mkdir(parents=True, exist_ok=True)
    file_path = Path(base_folder)
    file_name = f"{prefix}_{timestamp}.{ext}".replace(" ", "_")
    file_name = file_path / file_name  # type: ignore
    return file_name


def update_handler(
    logger: logging.Logger, log_file_name: str
) -> logging.Logger:
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            formatter = logger.handlers[0].formatter
            logger.removeHandler(handler)
            file_handler = logging.FileHandler(log_file_name)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    logger.info("Start of log file")
    return logger


if __name__ == "__main__":
    logger = create_logger()

    LOG_LENGTH = timedelta(hours=0, minutes=0, seconds=10)
    start_time = dt.now()
    while True:
        current_time = dt.now()
        if current_time - start_time > LOG_LENGTH:
            update_filename = new_filename()
            logger = update_handler(logger, update_filename)
            start_time = current_time
        else:
            logger = logger

        logger.info("before sleep")
        time.sleep(1)
        logger.warning("after sleep")
