import cv2
import socket
import struct
import pickle
import sys
import threading
import numpy as np
import AESGCM

CLIENT_NAME = sys.argv[1]

global active_socket
active_socket = {}


def get_system_info(info_socket):
    global active_socket
    window_name = CLIENT_NAME + ' Server Information'
    try:
        if info_socket:
            print('Device connected to server!')
            data = b""
            payload_size = struct.calcsize(">L")
            while True:
                while len(data) < payload_size:
                    packet = info_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += info_socket.recv(4 * 1024)
                system_info = data[:msg_size]
                data = data[msg_size:]
                system_info = pickle.loads(system_info)
                img = np.zeros((400, 400))
                for i in range(0, system_info[-1]):
                    cv2.putText(img, system_info[i], (20, (i + 1) * 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2,
                                cv2.LINE_AA)
                cv2.imshow(window_name, img)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    cv2.destroyWindow(window_name)
                    break


    except Exception as e:
        print('Exception:', str(e))
        info_socket.close()
        active_socket.pop('main')
        cv2.destroyWindow(window_name)


def connect_to_server():
    global active_socket
    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '127.0.0.1'  # Server IP
    port = 8000
    try:
        main_socket.connect((host_ip, port))
        identity = 'CLIENT-' + CLIENT_NAME
        main_socket.send(identity.encode('utf-8'))
        new_thread = threading.Thread(target=get_system_info, args=(main_socket,), daemon=True)
        new_thread.start()
        active_socket['main'] = main_socket
    except Exception as e:
        print('Exception:', str(e))
        print("Can't connect to server :(")


def receive_camera(camera_socket, camera_name):
    global active_socket
    window_name = CLIENT_NAME + ' ' + camera_name

    try:
        print('Received data from camera ' + camera_name + '!')
        data = b""
        payload_size = struct.calcsize(">L")

        # -- Get key for the camera data decryption -- #
        # -- Read key length -- #
        while len(data) < payload_size:
            packet = camera_socket.recv(32)
            if not packet:
                break
            data += packet
        key_msg_size = data[:payload_size]
        data = data[payload_size:]
        key_size = struct.unpack(">L", key_msg_size)[0]

        # -- Read key -- #
        while len(data) < key_size:
            data += camera_socket.recv(32)
        key = data[:key_size]
        data = data[key_size:]

        while True:
            # -- Read a packed message size -- #
            while len(data) < payload_size:
                packet = camera_socket.recv(4 * 1024)
                if not packet:
                    break
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # -- Read a encrypted frame -- #
            while len(data) < msg_size:
                data += camera_socket.recv(4 * 1024)
            encrypted_frame = data[:msg_size]
            data = data[msg_size:]

            frame_iv = encrypted_frame[0:12]
            frame_tag = encrypted_frame[12:28]
            frame_data = encrypted_frame[28:msg_size]

            decrypted_frame = AESGCM.decrypt(key, b"authenticated but not encrypted payload", frame_iv, frame_data, frame_tag)

            frame = pickle.loads(decrypted_frame)
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                cv2.destroyWindow(window_name)
                break

    except Exception as e:
        print('Exception:', str(e))
        active_socket.pop(camera_name)
        camera_socket.close()
        cv2.destroyWindow(window_name)

    active_socket.pop(camera_name)
    camera_socket.close()
    print('Stop Streaming', camera_name)


def request_camera(camera_name):
    global active_socket
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '127.0.0.1'
    port = 8000
    try:
        new_socket.connect((host_ip, port))
        identity = 'CLIENT-' + CLIENT_NAME + '-' + camera_name
        new_socket.send(identity.encode('utf-8'))
        new_thread = threading.Thread(target=receive_camera, args=(new_socket, camera_name), daemon=True)
        new_thread.start()
        active_socket[camera_name] = new_socket

    except Exception as e:
        print('Exception:', str(e))
        print("Can't get camera data :(")


while True:
    command = input('Enter command: ').strip().split(' ')

    if command[0] == 'connect':
        connect_to_server()
        continue

    if command[0] == 'close':
        print('Closing connection ...!')
        while len(active_socket) > 0:
            s = active_socket.popitem()
            s[1].close()
            print('')

    if command[0] == 'start':
        if not command[1] in active_socket:
            request_camera(command[1])
        else:
            print('Camera is streaming already!')

    if command[0] == 'stop':
        if command[1] in active_socket:
            active_socket[command[1]].close()
        else:
            print("Camera isn't connected!")

    if command[0] == 'exit':
        print('Exiting program ...!')
        break

    if command[0] == '':
        continue
    else:
        print('Undefined command!')


