import socket
import random
import time
import json

IP = "127.0.0.1"
PORT = 20000
E = 100
N = 100

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    rand_e = random.randint(300, 400) / 100
    rand_n = random.randint(300, 400) / 100
    E += rand_e
    N += rand_n
    time.sleep(1)
    msg = json.dumps((E, N))
    sock.sendto(msg.encode(), (IP, PORT))
    print(E, N)