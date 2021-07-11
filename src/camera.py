import cv2
import socket
import struct
import pickle
import sys

DEVICE_NAME = sys.argv[1]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST_IP = '127.0.0.1'
PORT = 8000
client_socket.connect((HOST_IP, PORT))
identity = 'CAMERA-' + DEVICE_NAME
client_socket.send(identity.encode('utf-8'))
# print("CAMERA CONNECTED TO SERVER!")

camera = sys.argv[2]
if camera == '0':
    vid = cv2.VideoCapture(0)
elif camera == '1':
    vid = cv2.VideoCapture('video/about.mp4')
img_counter = 0


while vid.isOpened():
    try:
        if client_socket:
            img, frame = vid.read()
            cv2.imshow('Camera Streaming', frame)
            key = cv2.waitKey(1)

            a = pickle.dumps(frame, 0)
            message = struct.pack(">L", len(a)) + a
            client_socket.sendall(message)
            img_counter += 1
            print("{}: {}".format(img_counter, len(message)))

    except Exception as e:
        pass

    key = cv2. waitKey(1) & 0xFF
    if key == 27:
        break

client_socket.close()
vid.release()
cv2.destroyAllWindows()