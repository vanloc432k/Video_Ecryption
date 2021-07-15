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

global keys
keys = {}

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
            global frame, keys
            data = b""
            payload_size = struct.calcsize(">L")

            # -- Get key for the camera data decryption -- #
            # -- Read key length -- #
            while len(data) < payload_size:
                packet = client_socket.recv(32)
                if not packet:
                    break
                data += packet
            key_msg_size = data[:payload_size]
            data = data[payload_size:]
            key_size = struct.unpack(">L", key_msg_size)[0]

            # -- Read key -- #
            while len(data) < key_size:
                data += client_socket.recv(32)
            key = data[:key_size]
            data = data[key_size:]
            keys[id] = key
            print(keys[id])

            while True:
                # -- Read a packed message size -- #
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                # -- Read a encrypted frame -- #
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                encrypted_frame = data[:msg_size]
                data = data[msg_size:]
                frame[id] = encrypted_frame

                # frame[id] = pickle.loads(frame_data)
                # window_name = 'Camera ' + id
                # cv2.imshow(window_name, frame[id])
                # key = cv2.waitKey(1) & 0xFF
                # if key == 27:
                #     break

    except Exception as e:
        print('Exception:', str(e))
        print(f"CAMERA {addr} DISCONNECTED")
        frame.pop(id)
        keys.pop(id)
        client_socket.close()


def serve_client(addr, client_socket, id):
    global active_clients
    try:
        print('CLIENT {} CONNECTED! '.format(addr))
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
            # -- Send camera key to client -- #
            key = keys[id]
            key_message = struct.pack(">L", len(key)) + key
            client_socket.sendall(key_message)

            # -- Stream encrypted frame to client -- #
            while True:
                if not(id in frame):
                    break
                encrypted_frame = frame[id]
                message = struct.pack(">L", len(encrypted_frame)) + encrypted_frame
                client_socket.sendall(message)

    except Exception as e:
        print('Exception:', str(e))
        print(f"CLIENT {addr} STOP STREAMING CAMERA {id}")
        client_socket.close()

    client_socket.close()

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
