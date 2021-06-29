import socket
import cv2 as cv

# Định nghĩa host và port mà server sẽ chạy và lắng nghe
from codecs import encode



#host = '127.0.0.1'
host = '0.0.0.0'
port = 6666

cap = cv.VideoCapture(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))

s.listen(1) # 1 ở đây có nghĩa chỉ chấp nhận 1 kết nối
print("Server listening on port", port)

c, addr = s.accept()
print("Connect from ", str(addr))

#server sử dụng kết nối gửi dữ liệu tới client dưới dạng binary
c.send(b"Hello, how are you, Hang")
#c.send("Bye", encode())
c.close()