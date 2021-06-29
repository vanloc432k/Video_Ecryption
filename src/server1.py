import socket
import cv2

HOST = '192.168.1.15'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print('Start listening...')
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        conn.sendall(b'Successfully connect!')
        while True:
            data = conn.recv(4096)
            if not data:
                conn.close()
                break
            else:
                cv2.imshow('Server', data)
            # conn.sendall(data)