# import standard libraries
from datetime import datetime as dt, timedelta
import logging
import queue
from typing import Dict
import time
import threading
# import package modules
import debug_logger


def get_log_length(settings: Dict) -> timedelta:
    log_length = settings["log_length"]
    log_length = timedelta(
        hours=int(log_length["hour"]),
        minutes=int(log_length["minute"]),
        seconds=int(log_length["second"]),
    )
    return log_length


def monitor_time(
    log_length: timedelta,
    logger: logging.Logger,
    time_q: queue.SimpleQueue,
):

    start_time = dt.now()
    while True:
        if not time_q.empty():
            get = time_q.get()
            if get == None:
                logger.critical(f"shutting down time {threading.current_thread().name}")
                break
        else:
            current_time = dt.now()
            if current_time - start_time > log_length:
                update_filename = debug_logger.new_filename()
                logger = debug_logger.update_handler(logger, update_filename)
                start_time = current_time
            else:
                logger = logger
                time.sleep(0.05)

def get_output_interval(settings: Dict) -> timedelta:
    output_interval = settings["output_interval"]
    output_interval = timedelta(
        hours=int(output_interval["hour"]),
        minutes=int(output_interval["minute"]),
        seconds=int(output_interval["second"]),
    )
    return output_interval


if __name__ == "__main__":
    import read_config

    q: queue.SimpleQueue = queue.SimpleQueue()
    # decision_maker_send_ss_q = 5
    settings = read_config.read_config_file("config.json")
    logger = debug_logger.create_logger()
    log_length = settings["log_length"]
    log_length = timedelta(
        hours=int(log_length["hour"]),
        minutes=int(log_length["minute"]),
        seconds=int(log_length["second"]),
    )

    monitor_time(log_length, logger, q)
