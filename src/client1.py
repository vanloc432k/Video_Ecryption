import cv2
import socket
import struct
import pickle
import sys
import threading
import numpy as np
import AESGCM
import tkinter as tk
import turtle

import numpy as np
from PIL import Image, ImageTk
import cv2

CLIENT_NAME = sys.argv[1]

global active_socket
active_socket = {}

global window   #cửa sổ chương trình
global canvas   #phần hiển thị video
global xb
global yb
global solver   #biến lưu after ( trong quá trình update canvas)
global lb1
global bt
global system_info

# CLIENT_NAME = sys.argv[1]

# global active_socket
# active_socket = {}

solver = None
bt = []
system_info = []

#tọa độ button camera đầu tiên
xb = 30
yb = 100

class MainWindow():         # xử lý nhấn mỗi button Camera
    def __init__(self, camera_name):
        global window
        global canvas
        global solver

        self.window = window
        self.canvas = canvas

        #xóa nội dung canvas để hiển thị mới
        self.canvas.delete("all")
        if solver is not None:
            self.canvas.after_cancel(solver)

        self.cap = cv2.VideoCapture("video/beauty.mp4")
        self.interval = 20 # Interval in ms to get the latest frame

        # Update image on canvas
        self.update_image()

    def update_image(self):
        #thay đổi ảnh hiển thị lên canvas
        global solver
        # Get the latest frame and convert image format
        _, frame = self.cap.read()
        frame = cv2.resize(frame, (500, 400))
        self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # to RGB
        self.image = Image.fromarray(self.image) # to PIL format
        self.image = ImageTk.PhotoImage(self.image) # to ImageTk format

        # Update image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)

        # Repeat every 'interval' ms
        solver = self.canvas.after(self.interval, self.update_image)

def receive_camera(camera_socket, camera_name):
    global active_socket
    global canvas
    global solver

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
            # _, frame = cv2.VideoCapture(0).read()
            frame = cv2.resize(frame, (500, 400))
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # to RGB
            image = Image.fromarray(image)  # to PIL format
            image = ImageTk.PhotoImage(image)  # to ImageTk format

            # Update image
            canvas.create_image(0, 0, anchor=tk.NW, image=image)

            # Repeat every 'interval' ms
            # solver = canvas.after(20, update_image)

            # cv2.imshow(window_name, frame)
            # stop_key = cv2.waitKey(1) & 0xFF
            # if stop_key == 27:
            #     cv2.destroyWindow(window_name)
            #     break

    except Exception as e:
        print('Exception:', str(e))
        active_socket.pop(camera_name)
        camera_socket.close()
        # cv2.destroyWindow(window_name)

    active_socket.pop(camera_name)
    camera_socket.close()
    print('Stop Streaming', camera_name)


def request_camera(camera_name):
    global active_socket
    global canvas
    global system_info
    global solver

    if camera_name in system_info:
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
    else:
        canvas.delete("all")
        if solver is not None:
            canvas.after_cancel(solver)
        canvas.create_text(100, 10, fill="white", font="Times 20 italic bold",
                           text=camera_name +" không còn hoạt động. Vui lòng Tải lại!")

def get_system_info(info_socket):
    global window
    global xb
    global yb
    global active_socket
    global bt
    global system_info

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
                # img = np.zeros((400, 400))
                # for i in range(0, system_info[-1]):
                #     bt = []
                #     bt.append(tk.Button(window, text=system_info[i], command=MainWindow))
                #     bt[i].place(x=xb, y=yb + i * 30)
                #     cv2.putText(img, system_info[i], (20, (i + 1) * 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2,
                #                 cv2.LINE_AA)
                # cv2.imshow(window_name, img)
                # key = cv2.waitKey(1) & 0xFF
                # if key == 27:
                #     cv2.destroyWindow(window_name)
                #     break


    except Exception as e:
        print('Exception:', str(e))
        info_socket.close()
        active_socket.pop('main')
        cv2.destroyWindow(window_name)

def reload():
    global window
    global system_info
    global bt

    if len(bt) > 0:
        for b in bt: b.destroy()
    for i in range(0, system_info[-1]):
        bt.append(tk.Button(window, text=system_info[i], command=lambda: request_camera(system_info[i])))
        bt[i].place(x=xb, y=yb + i * 30)


def connect_to_server():
    global active_socket
    global window

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

        # reload()
        rl = tk.Button(window, text="Tải lại", command=reload).place(x=0, y=0)
    except Exception as e:
        print('Exception:', str(e))
        print("Can't connect to server :(")

def begin():         #event click "Kết nối"
    global xb
    global yb

    for i in range(4):       #với mỗi camera tạo 1 button
        bt1 = tk.Button(window, text="Camera " + str(i), command=MainWindow)
        bt1.place(x = xb, y = yb + i*30)

def end():  #event click "Ngắt kết nối"
    global solver
    global canvas
    canvas.delete("all")
    canvas.after_cancel(solver)

if __name__ == "__main__":
    window = tk.Tk()
    window.title("Client")
    window.geometry("900x500+500+300")

    #tạo canvas
    canvas = tk.Canvas(window, bg="blue", width=500, height=400)
    canvas.place(x = 325, y = 80)

    lb1 = tk.Label(window, text="Danh sách camera: ", font=("", 18))
    lb1.place(x = 15, y = 50)

    bt_connect = tk.Button(window, text="Kết nối", command=connect_to_server)
    bt_connect.place(x = 150, y = 10)
    bt_disconnect = tk.Button(window, text="Ngắt kết nối", command=end)
    bt_disconnect.place(x = 500, y = 10)

    window.mainloop()