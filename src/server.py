import socket
import sys
import cv2
import pickle
import struct
import threading
import numpy as np

MAX_CONNECTIONS = 20

HOST = ''
PORT = 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

server_socket.bind((HOST, PORT))
print('Socket bind complete')
server_socket.listen(MAX_CONNECTIONS)
print('Socket now listening')

global frame
frame = {}

global active_clients
active_clients = []


def get_system_information():
    camera_list = list(frame.keys())
    camera_list.append(len(camera_list))
    return camera_list


def receive_camera(addr, client_socket, id):
    try:
        print('CAMERA {} CONNECTED!'.format(id))
        if client_socket:
            global frame
            data = b""
            payload_size = struct.calcsize(">L")
            while True:
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]

                frame[id] = pickle.loads(frame_data)
                window_name = 'Camera ' + id
                cv2.imshow(window_name, frame[id])
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break

    except Exception as e:
        print('Exception:', str(e))
        print(f"CAMERA {addr} DISCONNECTED")
        frame.pop(id)
        client_socket.close()


def serve_client(addr, client_socket, id):
    global active_clients
    try:
        print('CLIENT {} CONNECTED! '.format(addr))
        i = 0
        if client_socket:
            while True:
                sys_info = get_system_information()
                a = pickle.dumps(sys_info)
                message = struct.pack(">L", len(a)) + a
                client_socket.send(message)
                cv2.waitKey(1)

    except Exception as e:
        print('Exception:', str(e))
        print(f"CLIENT {addr} DISCONNECTED")
        active_clients.remove(id)
        client_socket.close()


def stream_to_client(addr, client_socket, id):
    global frame
    try:
        print(f'CLIENT {addr} STREAMING CAMERA {id}!')
        if client_socket:
            while True:
                a = pickle.dumps(frame[id])
                message = struct.pack(">L", len(a)) + a
                client_socket.sendall(message)

    except Exception as e:
        print('Exception:', str(e))
        print(f"CLIENT {addr} STOP STREAMING CAMERA {id}")
        client_socket.close()
        pass


while True:
    print("TOTAL CONNECTIONS:", threading.activeCount() - 1)
    print("TOTAL CAMERAS:", len(frame))
    print("TOTAL CLIENTS:", len(active_clients))

    client_socket, addr = server_socket.accept()
    identity = client_socket.recv(1024).decode('utf-8').split('-')
    print(identity)

    if identity[0] == 'CAMERA':
        frame[identity[1]] = None
        thread = threading.Thread(target=receive_camera, args=(addr, client_socket, identity[1]))
        thread.start()
    elif identity[0] == 'CLIENT':
        if identity[1] in active_clients:
            if identity[2] in frame:
                thread = threading.Thread(target=stream_to_client, args=(addr, client_socket, identity[2]))
                thread.start()
            else:
                client_socket.close()
        else:
            active_clients.append(identity[1])
            thread = threading.Thread(target=serve_client, args=(addr, client_socket, identity[1]))
            thread.start()
