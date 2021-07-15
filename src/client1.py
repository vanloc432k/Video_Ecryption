import socket
import struct
import pickle
import sys
import threading
import AESGCM
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
import cv2
from functools import partial

CLIENT_NAME = sys.argv[1]

global active_socket
active_socket = {}

global streaming_socket
streaming_socket = None

global window   #cửa sổ chương trình
global xb
global yb
global lb1
global buttons
global system_info
global current_frame

buttons = []
system_info = []

#tọa độ button camera đầu tiên
xb = 30
yb = 100

def do_nothing():
    pass

def popupError(s):
    popupRoot = tk.Tk()
    popupRoot.title("Error")
    popupButton = tk.Label(popupRoot, text = s, font = ("Verdana", 12))
    popupButton.pack()
    popupRoot.geometry('400x50+700+500')
    popupRoot.mainloop()

def receive_camera(camera_socket, camera_name):
    global active_socket
    global streaming_socket
    global current_frame

    # window_name = CLIENT_NAME + ' ' + camera_name

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
            frame = cv2.resize(frame, (500, 400))
            current_frame = frame

    except Exception as e:
        print('Exception:', str(e))
        if camera_name in active_socket:
            active_socket.pop(camera_name)
        camera_socket.close()
        streaming_socket = None
        current_frame = np.zeros((400, 500), np.float32)


def request_camera(camera_name):
    global active_socket
    global streaming_socket
    global system_info

    if not (camera_name in system_info):
        popupError("Camera không khả dụng! Vui lòng tải lại!")
    if camera_name == streaming_socket:
        popupError('Camera đang được hiển thị')
    else:
        print(streaming_socket)
        if streaming_socket is not None:
            active_socket[streaming_socket].close()
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
            streaming_socket = camera_name

        except Exception as e:
            print('Exception:', str(e))
            print("Can't get camera data :(")


def get_system_info(info_socket):
    global window
    global xb
    global yb
    global active_socket
    global buttons
    global system_info

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

    except Exception as e:
        print('Exception:', str(e))
        info_socket.close()
        if 'main' in active_socket:
            active_socket.pop('main')

def remove_button():
    global window
    global buttons

    if len(buttons) > 0:
        for b in buttons:
            b.destroy()
    buttons.clear()

def reload():
    global window
    global system_info
    global buttons

    if len(buttons) > 0:
        for b in buttons:
            b.destroy()
    buttons.clear()
    if 'main' in active_socket:
        print(system_info[-1])
        for i in range(0, system_info[-1]):
            camera_name = system_info[i]
            buttons.append(tk.Button(window, text=camera_name, command=partial(request_camera, camera_name)))
            buttons[i].place(x=xb, y=yb + i * 30)


def connect_to_server():
    global active_socket
    global window
    global current_frame

    if "main" in active_socket:
        popupError("Thiết bị đã được kết nối tới server!")
        return

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
        popupError("Không thể kết nối với server :( !")


def disconnect_from_server():  # event click "Ngắt kết nối"
    global active_socket
    global streaming_socket
    global current_frame
    streaming_socket = None
    current_frame = np.zeros((400, 500))

    while len(active_socket) > 0:
        s = active_socket.popitem()
        print(s)
        s[1].close()
    remove_button()


def update_image():
    global current_frame

    # -- Color Image -- #
    # image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
    # image = Image.fromarray(image, "RGB")

    # -- Gray Image -- #
    image = Image.fromarray(current_frame)

    image = ImageTk.PhotoImage(image)
    image_frame.imgtk = image
    image_frame.config(image=image)

    image_frame.after(10, update_image)


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Client " + CLIENT_NAME)
    window.geometry("900x500+500+300")

    current_frame = np.zeros((400, 500), np.float32)
    image_frame = tk.Label(window, bg="black", width=500, height=400)
    image_frame.place(x=325, y=80)

    lb1 = tk.Label(window, text="Danh sách camera: ", font=("", 18))
    lb1.place(x=15, y=50)

    bt_connect = tk.Button(window, text="Kết nối", command=connect_to_server)
    bt_connect.place(x=150, y=10)
    bt_disconnect = tk.Button(window, text="Ngắt kết nối", command=disconnect_from_server)
    bt_disconnect.place(x=500, y=10)

    tk.Button(window, text="Tải lại", command=reload).place(x=0, y=0)

    update_image()

    window.mainloop()

