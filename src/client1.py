import socket
import cv2

HOST = '192.168.1.15'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

cam = cv2.VideoCapture(0)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    noti = s.recv(1024)
    print(repr(noti.decode()))

    while(True):
        ret, f = cam.read()
        if ret==True:
            pic = cv2.cvtColor(f, 1)
            cv2.imshow('Client', pic)
            s.sendall(pic)
        else:
            break
        k = cv2.waitKey(1)
        if(k==113):
            break

    cam.release()
    cv2.destroyAllWindows()
    # s.sendall(b'Hello, world')
    # data = s.recv(1024)

# print('Received', repr(data))