import socket
import cv2

# Như mình đã nói ở trên thì chúng ta không truyền tham số vào vẫn ok
s = socket.socket()
s.connect(("192.168.1.15", 4000))
# s.connect(("100.72.89.226", 6666))

# 1024 là số bytes mà client có thể nhận được trong 1 lần
# Phần tin nhắn đầu tiên
img = s.recv(1024)

# Phần tin nhắn tiếp theo
while msg:
  print("Recvied ", msg.decode())
  msg = s.recv(1024)
s.close()

# bigdata: hadoop, spark
# network, linux, ssh, bash script: linux
# set up env, cài các thứ lib, dep
# conflict version, thữ
