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

import os
import random

from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)
from cryptography.hazmat.backends import default_backend


# Security parameter (fixed)
KEYLEN = 32

# Use crypto random generation to get a key with up to 3 random bytes
def gen(): 
    sysrand = random.SystemRandom()
    offset = sysrand.randint(1,32)
    key = bytearray(b'\x00'*(KEYLEN-offset)) 
    key.extend(os.urandom(offset))
    return bytes(key)

def encrypt(key, plaintext, associated_data):
    # Generate a random 96-bit IV.
    iv = os.urandom(12)

    # Construct an AES-GCM Cipher object with the given key and a
    # randomly generated IV.
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        default_backend()
    ).encryptor()

    # associated_data will be authenticated but not encrypted,
    # it must also be passed in on decryption.
    encryptor.authenticate_additional_data(associated_data)

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return (iv, ciphertext, encryptor.tag)

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
def encrypt_RSA(pk, plaintext):
    # Unpack the key into it's components
    key, n = pk
    # Convert each letter in the plaintext to numbers based on the character using a^b mod m
    cipher = [pow(ord(char), key, n) for char in plaintext]
    # Return the array of bytes
    return cipher
    
data_key = b""
payload_size_key = struct.calcsize(">L")
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
    
public= data_key[:msg_size]
data_key = data_key[msg_size:]
public = pickle.loads(public)
#print(public)
key = str(gen())
print(key)
key = encrypt_RSA(public, key)
#print(key)
key = pickle.dumps(key)
mess_key = struct.pack(">L", len(key)) + key
client_socket.sendall(mess_key)
print("send_key done")
while vid.isOpened():
    try:
        if client_socket:
            img, frame = vid.read()
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            stop_key = cv2.waitKey(1)
            a = pickle.dumps(frame, 0)
            iv, ciphertext, tag = encrypt(
                                            key,
                                            a,    
                                            b"authenticated but not encrypted payload"
                                        )
            mess_video = iv + tag +  ciphertext # a or ciphertext
            mess_video = struct.pack(">L", len(mess_video)) + mess_video
            #print(iv)
            #print(tag)
            client_socket.sendall(mess_video)


            #cv2.imshow('Camera Streaming', frame)

            img_counter += 1
            #print("{}: {}".format(img_counter, len(message)))
            #print(message)

    except Exception as e:
        pass

    stop_key = cv2. waitKey(1) & 0xFF
    if stop_key == 27:
        break

client_socket.close()
vid.release()
cv2.destroyAllWindows()