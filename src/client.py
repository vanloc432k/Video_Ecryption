import cv2
import socket
import struct
import pickle
import sys

REQUEST_DEVICE_NAME = sys.argv[1]
CLIENT_NAME = sys.argv[2]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1' # Server IP
port = 8000
client_socket.connect((host_ip, port))
request = 'CLIENT-' + REQUEST_DEVICE_NAME
client_socket.send(request.encode('utf-8'))
data = b""
print("CONNECTED TO SERVER!")
payload_size = struct.calcsize(">L")
while True:
    while len(data) < payload_size:
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
    window_name = "Client " + CLIENT_NAME
    cv2. imshow(window_name, frame)
    key = cv2. waitKey(1) & 0xFF
    if key == ord('q') :
        break
client_socket.close()