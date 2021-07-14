import cv2
import socket
import struct
import pickle
import sys
import AESGCM

# -- Set DEVICE NAME by command line -- #
DEVICE_NAME = sys.argv[1]

# -- Initialize socket and connect to server -- #
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST_IP = '127.0.0.1'
PORT = 8000
client_socket.connect((HOST_IP, PORT))

# -- Send device's identity & encryption key -- #
identity = 'CAMERA-' + DEVICE_NAME
client_socket.send(identity.encode('utf-8'))

# -- Get camera source -- #
camera = sys.argv[2]
if camera == '0':
    vid = cv2.VideoCapture(0)
elif camera == '1':
    vid = cv2.VideoCapture('video/about.mp4')

# -- Send encryption key -- #
key = AESGCM.gen()
key_message = struct.pack(">L", len(key)) + key
client_socket.sendall(key_message)

# -- Streaming loop -- #
while vid.isOpened():
    try:
        if client_socket:

            # -- Read & encrypt frame data -- #
            img, frame = vid.read()
            serialized_frame = pickle.dumps(frame, 0)
            iv, ciphertext, tag = AESGCM.encrypt(key, serialized_frame, b"authenticated but not encrypted payload")
            encrypted_frame = iv + tag + ciphertext
            message = struct.pack(">L", len(encrypted_frame)) + encrypted_frame
            client_socket.sendall(message)

            # -- Render frame for debugging -- #
            window_name = 'Camera ' + DEVICE_NAME + ' Streaming'
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

    except Exception as e:
        client_socket.close()
        vid.release()
        cv2.destroyAllWindows()
        print('Exception:', str(e))

client_socket.close()
vid.release()
cv2.destroyAllWindows()