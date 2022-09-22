import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0",20001))

while True:
    info = sock.recv(1024).decode()
    print(info)
