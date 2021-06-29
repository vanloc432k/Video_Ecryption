import cv2
import io
import socket
import struct
import time
import pickle
import zlib
import matplotlib.pyplot as plt

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.15', 8485))
connection = client_socket.makefile('wb')

cam = cv2.VideoCapture(0)

cam.set(3, 320);
cam.set(4, 240);

img_counter = 0

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

while True:
    ret, frame = cam.read()
    # pic = cv2.cvtColor(frame, 1)
    cv2.imshow('Client', frame)
    cv2.waitKey(1)
    # plt.imshow(frame)
    # plt.show()
    result, frame = cv2.imencode('.jpg', frame, encode_param)
    # cv2.imshow('Client', pic)
#    data = zlib.compress(pickle.dumps(frame, 0))
    data = pickle.dumps(frame, 0)
    size = len(data)

    print("{}: {}".format(img_counter, size))
    client_socket.sendall(struct.pack(">L", size) + data)
    img_counter += 1

cam.release()