import socket
import sys
import cv2
import pickle
import struct
import threading
# import imutils

HOST = '127.0.0.1'
PORT = 8000

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

server_socket.bind((HOST,PORT))
print('Socket bind complete')
server_socket.listen(10)
print('Socket now listening')

test_vid = cv2.VideoCapture('./video/about.mp4')
frame_counter = 0

global frame
frame = [None, None]

def start_video_stream () :
    global frame
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '127.0.0.1' # Camera IP
    port = 7000
    client_socket.connect((host_ip, port))
    data = b""
    payload_size = struct.calcsize(">L")

    while True :
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
        frame[0] = pickle.loads(frame_data)
        cv2.imshow("Server Serving", frame[0])
        key = cv2.waitKey(1) & 0xFF
        # print(data)
        if key == ord('q'):
            break
    client_socket.close()

thread = threading.Thread(target=start_video_stream, args=())
thread.start()

def serve_client (addr, client_socket):
    global frame
    try:
        print('CLIENT {} CONNECTED! '.format(addr))
        if client_socket:
            while True:
                a = pickle.dumps (frame[0])
                message = struct.pack(">L", len(a)) + a
                client_socket.sendall(message)

    except Exception as e:
        print (f"CLINET {addr} DISCONNECTED")
        pass

while True:
    client_socket, addr = server_socket.accept()
    print(addr)
    thread = threading.Thread(target=serve_client, args=(addr, client_socket))
    thread.start()

    print("TOTAL CLIENTS:", threading.activeCount() - 1)
