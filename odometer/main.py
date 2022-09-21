# built in libraries
import socket
from typing import Dict, List, Tuple
import queue
import time
import threading
import json
import math

# third-party libraries
import mysql.connector
from mysql.connector import Error

# variables
CONFIG = "config.json"

def read_config_file(filepath:str) -> Dict:
    with open(filepath, "r") as f:
        config = json.load(f)
    return config

def connect_to_database(database:Dict) -> mysql.connector:
    try:
        db = mysql.connector.connect(
            host=database["host"], 
            database=database["database"], 
            user=database["user"],
            password=database["password"]
        )
        if db.is_connected():  
            print(f"user: {database['user']} connected to database: {database['database']}")
            
            return db
        else:
            pass
    
    except Error as e:
        print(e)
        
def get_from_database(db:mysql.connector) -> List:
    cursor = db.cursor()
    cursor.execute("select e, n from odom order by id desc limit 1")
    x = cursor.fetchone()
    if x == None:
        return None
    else:
        return (float(x[0]), float(x[1]))
        
        
def insert_into_database(db:mysql.connector, position:List) -> None:
    cursor = db.cursor(buffered=True)
    e = f"{float(position[0]):.2f}"
    n = f"{float(position[1]):.2f}"
    cursor.execute("insert into odom (e, n) values (%s, %s)", (e, n))
    db.commit()
    
def insert_depth_into_database(db:mysql.connector, distance:float) -> None:
    cursor = db.cursor(buffered=True)
    cursor.execute(f"update odom set distance = {distance} where id = (select max(id) from odom)")
    db.commit()
    
def calc_new_odom(db:mysql.connector, distance:float) -> float:
    cursor = db.cursor(buffered=True)
    # get the previous odom value
    cursor.execute("select odometer from odom where id = ((select max(id) from odom) - 1)")
    old_odom = cursor.fetchone()
    print(old_odom)
    if old_odom[0] == None:
        old_odom = 0
    else:
        old_odom = float(old_odom[0])
    print(f"old odom = {old_odom}")
    
    if old_odom == None: old_odom = 0
    print(old_odom, distance)
    new_odom = old_odom + distance
    return new_odom


def insert_new_odom(db:mysql.connector, odom:float) -> None:
    cursor = db.cursor(buffered=True)
    cursor.execute(f"update odom set odometer = {odom} where id = (select max(id) from odom)")
    db.commit()

    
def get_data_from_nav(config, nav_q) -> None:
    connection = ("0.0.0.0", config["input"]["port"])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(connection)
    
    while True:
        position = eval(sock.recv(1024).decode())
        nav_q.put(position)
        print(position, type(position))
        time.sleep(0.5)
        
        
def worker(db, nav_q):
    
    while True:
        last_position = get_from_database(db)
        position = nav_q.get()
        insert_into_database(db, position)
        print(f"position inserted into database {position}")
        if last_position != None:
            distance = calc_dist_between_points(last_position, position)
            print(distance)
            insert_depth_into_database(db, distance)
            new_odom = calc_new_odom(db, distance)
            insert_new_odom(db, new_odom)
        else:
            pass
        
        
        
def calc_dist_between_points(old:Tuple, new:Tuple) -> float:
        delta_e = new[0] - old[0]
        delta_n = new[1] - old[1]
        distance = math.sqrt(delta_e**2 + delta_n**2)
        return distance
        
def main() -> None:
    # create qs for passing data between threads
    nav_q = queue.SimpleQueue() # data from nav
    # input_q = queue.SimpleQueue()
    # output_q = queue.SimpleQueue()
    # db_q = queue.SimpleQueue()
    
    config = read_config_file(CONFIG)
    db = connect_to_database(config["database"])
    
    nav_monitor = threading.Thread(target=get_data_from_nav, args=(config, nav_q))
    nav_monitor.start()
    
    # create a listening thread for commands from ROC
    
    # create a worker thread for processing and communication with database
    thr_worker = threading.Thread(target=worker, args=(db, nav_q))
    # create a sender thread for sending results to ROC
    thr_worker.start()
    nav_monitor.join()
    thr_worker.join()

if __name__ == "__main__":
    main()

