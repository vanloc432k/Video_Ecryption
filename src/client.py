import cv2
import io
import socket
import struct
import time
import pickle
import zlib
import matplotlib.pyplot as plt

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1' # Here Require CACHE Server IP
port = 8000
client_socket.connect((host_ip, port)) # a tuple
client_socket.send('Client'.encode('utf-8'))
data = b""
print("CONNECTED TO SERVER!")
payload_size = struct.calcsize(">L")
while True:
    while len (data) < payload_size:
        packet = client_socket.recv(4*1024)
        if not packet:
            break
        data += packet
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4*1024)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame = pickle.loads(frame_data)
    cv2. imshow("Client", frame)
    key = cv2. waitKey(1) & 0xFF
    if key == ord('q') :
        break
client_socket.close()