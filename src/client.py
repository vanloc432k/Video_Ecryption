import cv2
import socket
import struct
import pickle
import sys
import os
import random

from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)
from cryptography.hazmat.backends import default_backend


REQUEST_DEVICE_NAME = sys.argv[1]
CLIENT_NAME = sys.argv[2]

def decrypt(key, associated_data, iv, ciphertext, tag):
    # Construct a Cipher object, with the key, iv, and additionally the
    # GCM tag used for authenticating the message.
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        default_backend()
    ).decryptor()

    # We put associated_data back in or the tag will fail to verify
    # when we finalize the decryptor.
    decryptor.authenticate_additional_data(associated_data)

    # Decryption gets us the authenticated plaintext.
    # If the tag does not match an InvalidTag exception will be raised.
    return decryptor.update(ciphertext) + decryptor.finalize()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '127.0.0.1' # Server IP
port = 8000
client_socket.connect((host_ip, port))
request = 'CLIENT-' + REQUEST_DEVICE_NAME
client_socket.send(request.encode('utf-8'))
data_video = b""
data_iv = b""
data_tag = b""
data_key =  b""
print("CONNECTED TO SERVER!")
payload_size_video = struct.calcsize(">L")
payload_size_tag = struct.calcsize(">L")
payload_size_key = struct.calcsize(">L")
payload_size_iv = struct.calcsize(">L")

while len(data_key) < payload_size_key:
    packet = client_socket.recv(32)
    if not packet:
        break
    data_key += packet
packed_msg_size = data_key[:payload_size_key]
data_key = data_key[payload_size_key:]
msg_size = struct.unpack(">L", packed_msg_size)[0]
    
while len(data_key) < msg_size:
    data_key += client_socket.recv(32)
    #print(data_key)
    
frame_data_key = data_key[:msg_size]
data_key = data_key[msg_size:]
print(frame_data_key)
while True:

    # video
    while len(data_video) < payload_size_video:
        packet = client_socket.recv(4*1024)
        if not packet:
            break
        data_video += packet
    packed_msg_size = data_video[:payload_size_video]
    data_video = data_video[payload_size_video:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    
    while len(data_video) < msg_size:
        data_video += client_socket.recv(4*1024)
    #print(data_video)
    frame_data_video = data_video[:msg_size]
    data_video = data_video[msg_size:]

    frame_data_iv = frame_data_video[0:12]
    frame_data_tag = frame_data_video[12:28]
    frame_data_video = frame_data_video[28:msg_size]

    frame_data_video = decrypt(
    frame_data_key,
    b"authenticated but not encrypted payload",
    frame_data_iv,
    frame_data_video,
    frame_data_tag
    )

    frame = pickle.loads(frame_data_video)
    window_name = "Client " + CLIENT_NAME
    cv2.imshow(window_name, frame)
    stop_key = cv2. waitKey(1) & 0xFF
    if stop_key == 27 :
        break
client_socket.close()