# built in libraries
import socket
from typing import Dict, List, Tuple, Any
import queue
import time
import threading
import json
import math
from datetime import datetime as dt, timedelta
import logging

# third-party libraries
import mysql.connector  # type: ignore
from mysql.connector import Error

# import program modules
import debug_logger
import time_keeper

# variables
CONFIG = "config.json"


def read_config_file(filepath: str) -> Dict:
    with open(filepath, "r") as f:
        config = json.load(f)
    return config


def connect_to_database(logger: logging.Logger, database: Dict) -> mysql.connector:
    try:
        db = mysql.connector.connect(
            host=database["host"],
            database=database["database"],
            user=database["user"],
            password=database["password"],
        )
        if db.is_connected():
            logger.info(
                f"user: {database['user']} connected to database: {database['database']}"
            )

            return db
        else:
            pass

    except Error as e:
        print(e)


def get_from_database(logger: logging.Logger, db: mysql.connector) -> Tuple[Any, Any]:
    cursor = db.cursor()
    cursor.execute("select e, n from odom order by id desc limit 1")
    x = cursor.fetchone()
    if x == None:
        return (None, None)
    else:
        return (float(x[0]), float(x[1]))


def insert_into_database(
    logger: logging.Logger, db: mysql.connector, position: List
) -> None:
    cursor = db.cursor(buffered=True)
    e = f"{float(position[0]):.2f}"
    n = f"{float(position[1]):.2f}"
    cursor.execute("insert into odom (e, n) values (%s, %s)", (e, n))
    db.commit()


def insert_depth_into_database(
    logger: logging.Logger, db: mysql.connector, distance: float
) -> None:
    cursor = db.cursor(buffered=True)
    cursor.execute(
        f"update odom set distance = {distance} where id = (select max(id) from odom)"
    )
    db.commit()


def calc_new_odom(
    logger: logging.Logger, db: mysql.connector, distance: float
) -> float:
    cursor = db.cursor(buffered=True)
    # get the previous odom value
    cursor.execute(
        "select odometer from odom where id = ((select max(id) from odom) - 1)"
    )
    old_odom = cursor.fetchone()
    logger.info(f"last odometer reading read from db as {old_odom}")
    if old_odom[0] == None:
        old_odom = 0
        logger.debug("last odometer reading was NULL, setting as 0")
    else:
        old_odom = float(old_odom[0])

    if old_odom == None:
        old_odom = 0
    new_odom = old_odom + distance
    logger.info(f"new odometer reading is {new_odom}")
    return new_odom


def insert_new_odom(logger: logging.Logger, db: mysql.connector, odom: float) -> None:
    cursor = db.cursor(buffered=True)
    cursor.execute(
        f"update odom set odometer = {odom} where id = (select max(id) from odom)"
    )
    db.commit()
    logger.debug("new odometer inserted into db")


def get_data_from_nav(logger: logging.Logger, config, nav_q, kill_q) -> None:
    connection = ("0.0.0.0", config["input"]["port"])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(connection)

    while True:
        if not kill_q.empty():
            get = kill_q.get()
            if get == None:
                logger.critical(f"shutting down {threading.current_thread().name}")
                break
        else:
            position = eval(sock.recv(1024).decode())
            nav_q.put(position)
            logger.info(position)
            time.sleep(0.5)


def send_to_roc(
    logger: logging.Logger,
    config: Dict,
    msg: float,
    output_interval: timedelta,
    last_output_time: dt,
) -> dt:
    current_time = dt.now()
    if current_time - last_output_time > output_interval:
        last_output_time = current_time
        logger.debug("new_odom sent to ROC")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(
            f"current odometer: {msg:.2f}m".encode(),
            (config["roc"]["ip"], config["roc"]["port"]),
        )
        return last_output_time
    else:
        return last_output_time


def calc_dist_between_points(old: Tuple, new: Tuple) -> float:
    delta_e = new[0] - old[0]
    delta_n = new[1] - old[1]
    distance = math.sqrt(delta_e**2 + delta_n**2)
    return distance


def main() -> None:
    config = read_config_file(CONFIG)
    # create qs for passing data between threads
    nav_q: queue.SimpleQueue = queue.SimpleQueue()  # data from nav
    time_q: queue.SimpleQueue = queue.SimpleQueue()
    kill_q: queue.SimpleQueue = queue.SimpleQueue()

    logger = debug_logger.create_logger()

    log_length = time_keeper.get_log_length(config)
    time_monitor = threading.Thread(
        name="time_keeper",
        target=time_keeper.monitor_time,
        args=(log_length, logger, time_q),
    )
    time_monitor.start()

    db = connect_to_database(logger, config["database"])

    nav_monitor = threading.Thread(
        name="nav_monitor",
        target=get_data_from_nav,
        args=(logger, config, nav_q, kill_q),
    )
    nav_monitor.start()

    output_interval = time_keeper.get_output_interval(config)
    last_output_time = dt.now()
    while True:
        try:
            last_position = get_from_database(logger, db)
            position = nav_q.get()
            insert_into_database(logger, db, position)
            logger.info(f"position inserted into database {position}")
            if last_position[0] != None:
                distance = calc_dist_between_points(last_position, position)
                logger.info(f"distance calculated as {distance}")
                insert_depth_into_database(logger, db, distance)
                new_odom = calc_new_odom(logger, db, distance)
                insert_new_odom(logger, db, new_odom)
                last_output_time = send_to_roc(
                    logger, config, new_odom, output_interval, last_output_time
                )
            else:
                last_output_time = last_output_time
        except KeyboardInterrupt:
            time_q.put(None)
            kill_q.put(None)
            logger.critical("ctrl+c exitting program")
            break

    time_monitor.join()
    nav_monitor.join()


if __name__ == "__main__":
    main()