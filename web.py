import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("192.168.1.211", 443))
s.listen()
while True:
    conn = s.accept()
    print(conn)