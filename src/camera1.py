import cv2
import socket
import struct
import pickle

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = '127.0.0.1'
port = 7000
socket_address = (host_ip, port)
server_socket.bind(socket_address)
server_socket.listen()
print("Listening at", socket_address)

def start_video_stream():
    client_socket, addr = server_socket.accept()

    camera = True
    if camera == True:
        vid = cv2.VideoCapture(0)
    else:
        vid = cv2.VideoCapture('./video/about.mp4')
    vid.set(3, 320)
    vid.set(4, 240)

    img_counter = 0

    try:
        print('CLIENT {} CONNECTED!'.format(addr))
        if client_socket:
            while vid.isOpened():
                img, frame = vid.read()

                cv2.imshow('Camera Server', frame)
                key = cv2.waitKey(1) & 0xFF

                # result, frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

                data = pickle.dumps(frame, 0)
                size = len(data)
                print("{}: {}".format(img_counter, size))
                client_socket.sendall(struct.pack(">L", size) + data)
                img_counter += 1

                if key == ord('q'):
                    client_socket.close()
                    break

    except Exception as e:
        print(f"CACHE SERVER {addr} DISCONNECTED!")
        pass


while True:
    start_video_stream()