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

def decrypt_RSA(pk, ciphertext):
    # Unpack the key into its components
    key, n = pk
    # Generate the plaintext based on the ciphertext and key using a^b mod m
    aux = [str(pow(char, key, n)) for char in ciphertext]
    # Return the array of bytes as a string
    plain = [chr(int(char2)) for char2 in aux]
    return ''.join(plain)
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
    packet = client_socket.recv(4*1024)
    if not packet:
        break
    data_key += packet
packed_msg_size = data_key[:payload_size_key]
data_key = data_key[payload_size_key:]
msg_size = struct.unpack(">L", packed_msg_size)[0]
    
while len(data_key) < msg_size:
    data_key += client_socket.recv(4*1024)
    #print(data_key)

frame_data_key = data_key[:msg_size]
data_key = data_key[msg_size:]
frame_data_key = pickle.loads(frame_data_key)
#print(frame_data_key)
private = (302121813461474712046369310292560153919126167786976624158472486329566331232724257278824680667138394928960485682494264929339967633092240174342018754140785269142736578265388015658508710597670528886451587273561602492176936318769547341019177979425636968449600894389248202666068055289172246035177348394572497824460924300670209800669987601770133311855807825914417640609920322651518806667304713082550573569192474630520136510367815645508397516556245736428844052847042214360890025661187280725860059635439585886404011276968734556518505365854930092122274198871992585167243288799313257205383922966292114284972069336073033848158326492413914656243790454337506146337611098482375130957405823136380246454598763587514240341587551535903184517795720126955168464808767319601745021292958025560097466838572023018400549134932382972566344987047333424715563238942491508314648953691757907168218309599018580281766904138855278381759813840981930691532572162186003324088381144297512746756529737448877274376182557023526630742536442574151627892206098238940141221300599254638218595992172189959962969581006463857798982498342641969296274652416228067556273203049096137288333199903968591601248041312409568295028387805445642794694088555194295889221476407184211337597715833, 219093950390798403036289525572954632872332136266757889132905408780532995631746612865658827066852468830488940743922390866239349246021186409088540928423286729741405197027547449692787855441262711283786639677845577836622112813333446230495842561727201228588876301437398397603116637595166183893927532952019456542463772490695313549498771477256327409638511000933997396192743894873446230159298054322073517185119898505530951097273031699437483326190977738116122319641451344256387883740997947434657107500945744363477387063532620009972794121944270632076352493275194764821466750693682955966581292212724142620742841455603356946725809742953827771221200005221962369269233013118971280927971323071135428599735312829396104292549848290193432448740290288677391023485362327869331277527248066924936126325453639718331582337356815916542467501123460535794740390196081615522355778584821394978809459620116881153812397323468353081956148242920067189151985775111970638164046085743050333498716824042032359969168016321239911277681418918002135109467636009383003153169389373201933692753426269516811966358290703345504357895271300236310324339596234709407219913040398978657643179550994772529364226641373856365896334583807941080744621294017297343581930031867977227549270243)
frame_data_key = decrypt_RSA(private, frame_data_key)
print("Load key done")
print(frame_data_key)
OK = b'OK'
mess_OK = struct.pack(">L", len(OK)) + OK
client_socket.sendall(mess_OK)
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