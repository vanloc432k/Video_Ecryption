import socket
import sys
import cv2
import pickle
import struct
import threading
import numpy as np

'''
-----BEGIN PUBLIC KEY-----
MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAlOwMCeIziY3nEfF7XWJY
UxEYHzASGJbSMiaQMXT0QNjVg0uJqd5MFNAZ2csaPe5KP11ZUoo84GeDRgRErv2w
GWkO/OmHYdIB6Q/LdC2hUh8orGZQzstAL5SDkwErsXO8PXH98tqQEx3ytT4vQcQR
3gE0dvI2E7btseV1uhcT9N6EySB73ICNbH7+PAd3PXLtSBJkEQr8To55eP/gdZ1G
SNGfNrbNJSMX2kxz3/qNk3086sByKNTco1NxMvTvdjNnXedjigEm/nHlovXdzjaO
7dgQltFqoIwk+YjT8Zvz/tr+U0429koDbADeOvo3siYhTr4Hv+puI6Uy4iZ/C57P
BsADQb7i7bVnPg8HNjuKe5iqzF3KqnOel9rPwSjjEfKE+zuHddPSiW3+WtgdGSpa
OD5BerCehT2/fb6dg8hGqdCW5ZsERbYzHaEcSggydLjDsrc56NMYm0cXSnjHDU2Q
CnBTZqQeXrLk7dEzh4Xl7mK2EMWtSDA9M6e7P7sTFM/xAgMBAAE=
-----END PUBLIC KEY-----
'''

MAX_CONNECTIONS = 20

HOST = ''
PORT = 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

server_socket.bind((HOST, PORT))
print('Socket bind complete')
server_socket.listen(MAX_CONNECTIONS)
print('Socket now listening')

global frame
frame = {}

global keys
keys = {}

global active_clients
active_clients = []

global public_key
public_key = (12199278499564376403653338592210183144703088572156824430164245293136216729076493706413403301552363072923675085695807080299704620224038662013598514562222962507844683708184916981010885861322386204643159861169156701058905162244240461270071601711850578021341940543270997969167649254212643269926888407165069640820443278076080675389082577598447426552502401410120810793550957474296663355530622094976249983474655015688921505920803793447669894165826618533010531301724918509551367974765872364808856293633885161068009407969318782214479952919634103954593293163271570109972766030126454898288185339240076781630056330159995629524312324968707260847673516164203844564109745504807759565922916795735185649230927880869870671442738875174706110895824693443165570619132481056534097364673614271329211275392601688620671700151223828857500687779616522290500353768985574620808168646422475701538528933043991815564859967644993100009170426073756285285426204395332436938309992936472550992785791561282995651561617836298915285983124593250650119273608708878779947625343460552368287701885270574358253663511629740695115103933615997997586341751489306050587951072333036519212998483984830385496789644490583817784694101285496168114859542119066462648978744182996738604285897,
219093950390798403036289525572954632872332136266757889132905408780532995631746612865658827066852468830488940743922390866239349246021186409088540928423286729741405197027547449692787855441262711283786639677845577836622112813333446230495842561727201228588876301437398397603116637595166183893927532952019456542463772490695313549498771477256327409638511000933997396192743894873446230159298054322073517185119898505530951097273031699437483326190977738116122319641451344256387883740997947434657107500945744363477387063532620009972794121944270632076352493275194764821466750693682955966581292212724142620742841455603356946725809742953827771221200005221962369269233013118971280927971323071135428599735312829396104292549848290193432448740290288677391023485362327869331277527248066924936126325453639718331582337356815916542467501123460535794740390196081615522355778584821394978809459620116881153812397323468353081956148242920067189151985775111970638164046085743050333498716824042032359969168016321239911277681418918002135109467636009383003153169389373201933692753426269516811966358290703345504357895271300236310324339596234709407219913040398978657643179550994772529364226641373856365896334583807941080744621294017297343581930031867977227549270243)


def get_system_information():
    camera_list = list(frame.keys())
    camera_list.append(len(camera_list))
    return camera_list


def receive_camera(addr, client_socket, id):
    try:
        print('CAMERA {} CONNECTED!'.format(id))
        if client_socket:
            global frame, keys, public_key
            data = b""
            payload_size = struct.calcsize(">L")

            serialized_public_key = pickle.dumps(public_key, 0)
            public_key_message = struct.pack(">L", len(serialized_public_key)) + serialized_public_key
            client_socket.sendall(public_key_message)

            # -- Get key for the camera data decryption -- #
            # -- Read key length -- #
            while len(data) < payload_size:
                packet = client_socket.recv(32)
                if not packet:
                    break
                data += packet
            key_msg_size = data[:payload_size]
            data = data[payload_size:]
            key_size = struct.unpack(">L", key_msg_size)[0]

            # -- Read key -- #
            while len(data) < key_size:
                data += client_socket.recv(32)
            key = data[:key_size]
            data = data[key_size:]
            keys[id] = key
            # print('received encrypted key')
            while True:
                # -- Read a packed message size -- #
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                # -- Read a encrypted frame -- #
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                encrypted_frame = data[:msg_size]
                data = data[msg_size:]
                frame[id] = encrypted_frame

    except Exception as e:
        print('Exception:', str(e))
        print(f"CAMERA {addr} DISCONNECTED")
        frame.pop(id)
        keys.pop(id)
        client_socket.close()


def serve_client(addr, client_socket, id):
    global active_clients
    try:
        print('CLIENT {} CONNECTED! '.format(addr))
        if client_socket:
            while True:
                sys_info = get_system_information()
                a = pickle.dumps(sys_info)
                message = struct.pack(">L", len(a)) + a
                client_socket.send(message)
                cv2.waitKey(1)

    except Exception as e:
        print('Exception:', str(e))
        print(f"CLIENT {addr} DISCONNECTED")
        active_clients.remove(id)
        client_socket.close()


def stream_to_client(addr, client_socket, id):
    global frame
    try:
        print(f'CLIENT {addr} STREAMING CAMERA {id}!')
        if client_socket:
            # -- Send camera key to client -- #
            key = keys[id]
            key_message = struct.pack(">L", len(key)) + key
            client_socket.sendall(key_message)
            # print('sent key to client')
            # -- Stream encrypted frame to client -- #
            while True:
                if not(id in frame):
                    break
                encrypted_frame = frame[id]
                message = struct.pack(">L", len(encrypted_frame)) + encrypted_frame
                client_socket.sendall(message)

    except Exception as e:
        print('Exception:', str(e))
        print(f"CLIENT {addr} STOP STREAMING CAMERA {id}")
        client_socket.close()

    client_socket.close()

while True:
    print("TOTAL CONNECTIONS:", threading.activeCount() - 1)
    print("TOTAL CAMERAS:", len(frame))
    print("TOTAL CLIENTS:", len(active_clients))

    client_socket, addr = server_socket.accept()
    identity = client_socket.recv(1024).decode('utf-8').split('-')
    print(identity)

    if identity[0] == 'CAMERA':
        frame[identity[1]] = None
        thread = threading.Thread(target=receive_camera, args=(addr, client_socket, identity[1]))
        thread.start()
    elif identity[0] == 'CLIENT':
        if identity[1] in active_clients:
            if identity[2] in frame:
                thread = threading.Thread(target=stream_to_client, args=(addr, client_socket, identity[2]))
                thread.start()
            else:
                client_socket.close()
        else:
            active_clients.append(identity[1])
            thread = threading.Thread(target=serve_client, args=(addr, client_socket, identity[1]))
            thread.start()
