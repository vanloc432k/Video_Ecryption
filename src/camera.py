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
    vid = cv2.VideoCapture('video/beauty.mp4')

def encrypt_RSA(pk, plaintext):
    # Unpack the key into it's components
    key, n = pk
    # Convert each letter in the plaintext to numbers based on the character using a^b mod m
    cipher = [pow(ord(char), key, n) for char in plaintext]
    # Return the array of bytes
    return cipher

# -- Wait for public key from server for RSA encryption -- #
data_key = b""
payload_size = struct.calcsize(">L")
while len(data_key) < payload_size:
    packet = client_socket.recv(32)
    if not packet:
        break
    data_key += packet
packed_msg_size = data_key[:payload_size]
data_key = data_key[payload_size:]
msg_size = struct.unpack(">L", packed_msg_size)[0]

while len(data_key) < msg_size:
    data_key += client_socket.recv(32)

public_key = data_key[:msg_size]
data_key = data_key[msg_size:]
public_key = pickle.loads(public_key)


# -- Generate encryption key & send to server -- #
key = AESGCM.gen()
print(key)
encrypted_key = encrypt_RSA(public_key, str(key, encoding='latin-1'))
print(encrypted_key)

serialized_key = pickle.dumps(encrypted_key)
key_message = struct.pack(">L", len(serialized_key)) + serialized_key
client_socket.sendall(key_message)
print('send key done')
# -- Streaming loop -- #
while vid.isOpened():
    try:
        if client_socket:

            # -- Read & encrypt frame data -- #
            img, frame = vid.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            serialized_frame = pickle.dumps(frame, 0)
            iv, ciphertext, tag = AESGCM.encrypt(key, serialized_frame, b"authenticated but not encrypted payload")
            encrypted_frame = iv + tag + ciphertext
            message = struct.pack(">L", len(encrypted_frame)) + encrypted_frame
            client_socket.sendall(message)

            # -- Render frame for debugging -- #
            # window_name = 'Camera ' + DEVICE_NAME + ' Streaming'
            # cv2.imshow(window_name, frame)
            # stop_key = cv2.waitKey(1) & 0xFF
            # if stop_key == 27:
            #     break

    except Exception as e:
        client_socket.close()
        vid.release()
        # cv2.destroyAllWindows()
        print('Exception:', str(e))

client_socket.close()
vid.release()
# cv2.destroyAllWindows()