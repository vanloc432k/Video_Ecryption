import cv2
#import matplotlib.pyplot as plt
import socket

host = '0.0.0.0'
port = 4000

cam = cv2.VideoCapture(0)

while(True):
    ret, f = cam.read()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    s.listen(1)  # 1 ở đây có nghĩa chỉ chấp nhận 1 kết nối
    print("Server listening on port", port)

    c, addr = s.accept()
    print("Connect from ", str(addr))

    if ret == True:
        pic = cv2.cvtColor(f, 1)

        img = cv2.resize(f, (0,0), fx=0.5, fy=0.5)
        cv2.imwrite('temp.png', img)
        c.send(pic)
        cv2.imshow('Camera', pic)
        # cv2.imshow('Camera', f)
    else:
        break
    k = cv2.waitKey(1)
    if(k == 113):
        c.close()
        break

cam.release()
cv2.destroyAllWindows()