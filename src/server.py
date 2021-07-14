from random import triangular
import socket
import sys
from typing_extensions import IntVar
import cv2
import pickle
import struct
import threading
# import imutils

HOST = '127.0.0.1'
PORT = 8000

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

server_socket.bind((HOST, PORT))
print('Socket bind complete')
server_socket.listen()
print('Socket now listening')

global frame
global data_key
global data_iv
global data_tag
global data_video
frame_video = {}
frame_tag = {}
frame_key = {}
frame_iv = {}
list_accept_ip = []
def receive_camera(addr, client_socket, id):
    global frame
    data_video = b""
    global key 
    data_key = b""
    global tag 
    data_tag = b""
    global iv 
    data_iv = b""
    payload_size_key = struct.calcsize(">L")
    payload_size_video = struct.calcsize(">L")
    payload_size_tag = struct.calcsize(">L")
    payload_size_iv = struct.calcsize(">L")

    while len(data_key) < payload_size_key:
        packet = client_socket.recv(32)
        if not packet:
            break
        data_key += packet
    packed_msg_size = data_key[:payload_size_key]
    data_key = data_key[payload_size_key:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(data_key) < msg_size:
        data_key += client_socket.recv(32)
    frame_data_key = data_key[:msg_size]
    data_key = data_key[msg_size:]
    frame_key[id] = frame_data_key
    print(frame_key[id])

    while True:

        #frame
        while len(data_video) < payload_size_video:
            packet = client_socket.recv(4 * 1024)
            if not packet:
                break
            data_video += packet
        packed_msg_size = data_video[:payload_size_video]
        data_video = data_video[payload_size_video:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        while len(data_video) < msg_size:
            data_video += client_socket.recv(4 * 1024)
        frame_data_video = data_video[:msg_size]
        #print(frame_data_video[0:12])
        #print(frame_data_video[12:28])
        data_video = data_video[msg_size:]
        frame_video[id] = frame_data_video

        stop_key = cv2.waitKey(1) & 0xFF
        if stop_key == ord('q'):
            print("break")
            break
    frame_video.pop(id)
    client_socket.close()

def serve_client (addr, client_socket, id):
    global frame_video
    global frame_key
    global frame_iv
    global frame_tag
    try:
        print('CLIENT {} CONNECTED! '.format(addr))
        if client_socket:
            a = frame_key[id]
            print(a)
            mess_key = struct.pack(">L", len(a)) + a
            client_socket.sendall(mess_key)

            while True:

                a = frame_video[id]
                mess_video = struct.pack(">L", len(a)) + a
                client_socket.sendall(mess_video)

    except Exception as e:
        print (f"CLIENT {addr} DISCONNECTED")
        pass

def system_information():
    print(frame_video)
    pass

while True:
    client_socket, addr = server_socket.accept()
    identity = client_socket.recv(1024).decode('utf-8').split('-')
    print(identity)
    if identity[0] == 'CAMERA':
        print('Camera', addr)
        frame_iv[identity[1]] = None
        frame_tag[identity[1]] = None
        frame_video[identity[1]] = None
        thread = threading.Thread(target=receive_camera, args=(addr, client_socket, identity[1]))
        thread.start()
    elif identity[0] == 'CLIENT':
        print('Client', addr)
        thread = threading.Thread(target=serve_client, args=(addr, client_socket, identity[1]))
        thread.start()

    print("TOTAL CONNECTIONS:", threading.activeCount())

