import pickle
import socket
import struct
import sys
import threading
import tkinter as tk
import turtle

import numpy as np
from PIL import Image, ImageTk
import cv2

global window   #cửa sổ chương trình
global canvas   #phần hiển thị video
global xb
global yb
global solver   #biến lưu after ( trong quá trình update canvas)
global lb1

# CLIENT_NAME = sys.argv[1]

# global active_socket
# active_socket = {}

solver = None

#tọa độ button camera đầu tiên
xb = 30
yb = 100

class MainWindow():         # xử lý nhấn mỗi button Camera
    def __init__(self):
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
        # self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        # self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.interval = 20 # Interval in ms to get the latest frame

        # Create canvas for image
        # self.canvas = tk.Canvas(self.window, width=300, height=200)
        # self.canvas.grid(row=row, column=col)

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

# def get_system_info(info_socket):
#     global active_socket
#     try:
#         if info_socket:
#             print('Device connected to server!')
#             data = b""
#             payload_size = struct.calcsize(">L")
#             while True:
#                 while len(data) < payload_size:
#                     packet = info_socket.recv(4 * 1024)
#                     if not packet:
#                         break
#                     data += packet
#                 packed_msg_size = data[:payload_size]
#                 data = data[payload_size:]
#                 msg_size = struct.unpack(">L", packed_msg_size)[0]
#
#                 while len(data) < msg_size:
#                     data += info_socket.recv(4 * 1024)
#                 system_info = data[:msg_size]
#                 data = data[msg_size:]
#                 system_info = pickle.loads(system_info)
#                 img = np.zeros((400, 400))
#                 for i in range(0, system_info[-1]):
#                     cv2.putText(img, system_info[i], (20, (i + 1) * 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2,
#                                 cv2.LINE_AA)
#                 window_name = CLIENT_NAME + ' Server Information'
#                 cv2.imshow(window_name, img)
#                 key = cv2.waitKey(1) & 0xFF
#                 if key == 27:
#                     cv2.destroyWindow(window_name)
#                     break
#
#
#     except Exception as e:
#         print('Exception:', str(e))
#         info_socket.close()
#         active_socket.pop('main')
#
#
# def connect_to_server():
#     global active_socket
#     main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     host_ip = '127.0.0.1'  # Server IP
#     port = 8000
#     try:
#         main_socket.connect((host_ip, port))
#         identity = 'CLIENT-' + CLIENT_NAME
#         main_socket.send(identity.encode('utf-8'))
#         new_thread = threading.Thread(target=get_system_info, args=(main_socket,), daemon=True)
#         new_thread.start()
#         active_socket['main'] = main_socket
#     except Exception as e:
#         print('Exception:', str(e))
#         print("Can't connect to server :(")

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

    bt_connect = tk.Button(window, text="Kết nối", command=begin)
    bt_connect.place(x = 150, y = 10)
    bt_disconnect = tk.Button(window, text="Ngắt kết nối", command=end)
    bt_disconnect.place(x = 500, y = 10)

    window.mainloop()