import socket
import struct
import pickle
import sys
import threading
import AESGCM
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
import cv2
from functools import partial

CLIENT_NAME = sys.argv[1]
global HOST_IP
global PORT
HOST_IP = '127.0.0.1'
PORT = 8000

global active_socket
active_socket = {}

global streaming_socket
streaming_socket = None

global private_key
private_key = (302121813461474712046369310292560153919126167786976624158472486329566331232724257278824680667138394928960485682494264929339967633092240174342018754140785269142736578265388015658508710597670528886451587273561602492176936318769547341019177979425636968449600894389248202666068055289172246035177348394572497824460924300670209800669987601770133311855807825914417640609920322651518806667304713082550573569192474630520136510367815645508397516556245736428844052847042214360890025661187280725860059635439585886404011276968734556518505365854930092122274198871992585167243288799313257205383922966292114284972069336073033848158326492413914656243790454337506146337611098482375130957405823136380246454598763587514240341587551535903184517795720126955168464808767319601745021292958025560097466838572023018400549134932382972566344987047333424715563238942491508314648953691757907168218309599018580281766904138855278381759813840981930691532572162186003324088381144297512746756529737448877274376182557023526630742536442574151627892206098238940141221300599254638218595992172189959962969581006463857798982498342641969296274652416228067556273203049096137288333199903968591601248041312409568295028387805445642794694088555194295889221476407184211337597715833, 219093950390798403036289525572954632872332136266757889132905408780532995631746612865658827066852468830488940743922390866239349246021186409088540928423286729741405197027547449692787855441262711283786639677845577836622112813333446230495842561727201228588876301437398397603116637595166183893927532952019456542463772490695313549498771477256327409638511000933997396192743894873446230159298054322073517185119898505530951097273031699437483326190977738116122319641451344256387883740997947434657107500945744363477387063532620009972794121944270632076352493275194764821466750693682955966581292212724142620742841455603356946725809742953827771221200005221962369269233013118971280927971323071135428599735312829396104292549848290193432448740290288677391023485362327869331277527248066924936126325453639718331582337356815916542467501123460535794740390196081615522355778584821394978809459620116881153812397323468353081956148242920067189151985775111970638164046085743050333498716824042032359969168016321239911277681418918002135109467636009383003153169389373201933692753426269516811966358290703345504357895271300236310324339596234709407219913040398978657643179550994772529364226641373856365896334583807941080744621294017297343581930031867977227549270243)

global window
global buttons
global system_info
global current_frame

buttons = []
system_info = []

def decrypt_RSA(pk, ciphertext):
    # Unpack the key into its components
    key, n = pk
    # Generate the plaintext based on the ciphertext and key using a^b mod m
    aux = [str(pow(char, key, n)) for char in ciphertext]
    # Return the array of bytes as a string
    plain = [chr(int(char2)) for char2 in aux]
    return ''.join(plain)


def do_nothing():
    pass


def popupError(s):
    popupRoot = tk.Tk()
    popupRoot.title("Error")
    popupButton = tk.Label(popupRoot, text = s, font = ("Verdana", 12))
    popupButton.pack()
    popupRoot.geometry('400x50+700+500')
    popupRoot.mainloop()


def receive_camera(camera_socket, camera_name):
    global active_socket
    global streaming_socket
    global current_frame
    global private_key

    # window_name = CLIENT_NAME + ' ' + camera_name

    try:
        print('Received data from camera ' + camera_name + '!')
        data = b""
        payload_size = struct.calcsize(">L")

        # -- Get key for the camera data decryption -- #
        # -- Read key length -- #
        while len(data) < payload_size:
            packet = camera_socket.recv(32)
            if not packet:
                break
            data += packet
        key_msg_size = data[:payload_size]
        data = data[payload_size:]
        key_size = struct.unpack(">L", key_msg_size)[0]

        # -- Read & decrypt key -- #
        while len(data) < key_size:
            data += camera_socket.recv(32)
        encrypted_key = data[:key_size]
        data = data[key_size:]
        # print('got encrypted key')

        deserialized_key = pickle.loads(encrypted_key)
        decrypted_key = decrypt_RSA(private_key, deserialized_key)
        print(decrypted_key)
        decrypted_key = str.lstrip(decrypted_key, "b'")
        decrypted_key = str.lstrip(decrypted_key, "'")
        print(decrypted_key)
        key = bytes(decrypted_key.encode('latin-1'))
        print(key)

        while True:
            # -- Read a packed message size -- #
            while len(data) < payload_size:
                packet = camera_socket.recv(4 * 1024)
                if not packet:
                    break
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # -- Read a encrypted frame -- #
            while len(data) < msg_size:
                data += camera_socket.recv(4 * 1024)
            encrypted_frame = data[:msg_size]
            data = data[msg_size:]

            frame_iv = encrypted_frame[0:12]
            frame_tag = encrypted_frame[12:28]
            frame_data = encrypted_frame[28:msg_size]

            decrypted_frame = AESGCM.decrypt(key, b"authenticated but not encrypted payload", frame_iv, frame_data, frame_tag)

            frame = pickle.loads(decrypted_frame)
            # frame = cv2.resize(frame, (768, 432))
            current_frame = frame

    except Exception as e:
        print('Exception:', str(e))
        if camera_name in active_socket:
            active_socket.pop(camera_name)
        camera_socket.close()
        streaming_socket = None
        current_frame = np.zeros((400, 500), np.float32)


def request_camera(camera_name):
    global HOST_IP
    global PORT
    global active_socket
    global streaming_socket
    global system_info

    if not (camera_name in system_info):
        popupError("Camera không khả dụng! Vui lòng tải lại!")
    if camera_name == streaming_socket:
        popupError('Camera đang được hiển thị')
    else:
        print(streaming_socket)
        if streaming_socket is not None:
            active_socket[streaming_socket].close()
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            new_socket.connect((HOST_IP, PORT))
            identity = 'CLIENT-' + CLIENT_NAME + '-' + camera_name
            new_socket.send(identity.encode('utf-8'))
            new_thread = threading.Thread(target=receive_camera, args=(new_socket, camera_name), daemon=True)
            new_thread.start()
            active_socket[camera_name] = new_socket
            streaming_socket = camera_name

        except Exception as e:
            print('Exception:', str(e))
            print("Can't get camera data :(")


def get_system_info(info_socket):
    global window
    global xb
    global yb
    global active_socket
    global buttons
    global system_info

    try:
        if info_socket:
            print('Device connected to server!')
            data = b""
            payload_size = struct.calcsize(">L")
            while True:
                while len(data) < payload_size:
                    packet = info_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += info_socket.recv(4 * 1024)
                system_info = data[:msg_size]
                data = data[msg_size:]
                system_info = pickle.loads(system_info)

    except Exception as e:
        print('Exception:', str(e))
        info_socket.close()
        if 'main' in active_socket:
            active_socket.pop('main')

def remove_button():
    global window
    global buttons

    if len(buttons) > 0:
        for b in buttons:
            b.destroy()
    buttons.clear()

def reload():
    global window
    global system_info
    global buttons

    if len(buttons) > 0:
        for b in buttons:
            b.destroy()
    buttons.clear()
    if 'main' in active_socket:
        print(system_info[-1])
        for i in range(0, system_info[-1]):
            camera_name = system_info[i]
            buttons.append(tk.Button(window, height=1, width=20, text=camera_name, command=partial(request_camera, camera_name)))
            buttons[i].place(x=20 + int(i / 10)*30, y=120 + int(i % 10)*30)


def connect_to_server():
    global HOST_IP
    global PORT
    global active_socket
    global window
    global current_frame

    if "main" in active_socket:
        popupError("Thiết bị đã được kết nối tới server!")
        return

    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        main_socket.connect((HOST_IP, PORT))
        identity = 'CLIENT-' + CLIENT_NAME
        main_socket.send(identity.encode('utf-8'))
        new_thread = threading.Thread(target=get_system_info, args=(main_socket,), daemon=True)
        new_thread.start()
        active_socket['main'] = main_socket

    except Exception as e:
        print('Exception:', str(e))
        popupError("Không thể kết nối với server :( !")


def disconnect_from_server():  # event click "Ngắt kết nối"
    global active_socket
    global streaming_socket
    global current_frame
    streaming_socket = None
    current_frame = np.zeros((400, 500))

    while len(active_socket) > 0:
        s = active_socket.popitem()
        s[1].close()
    remove_button()


def update_image():
    global current_frame

    bounding_width = image_frame['width']
    bounding_height = image_frame['height']
    resize_ratio = 1
    if current_frame.shape[1]/current_frame.shape[0] > bounding_width/bounding_height:
        resize_ratio = bounding_width/current_frame.shape[1]
    else:
        resize_ratio = bounding_height/current_frame.shape[0]
    frame = cv2.resize(current_frame, (int(current_frame.shape[1]*resize_ratio), int(current_frame.shape[0]*resize_ratio)))

    # -- Color Image -- #
    # image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # image = Image.fromarray(image, "RGB")

    # -- Gray Image -- #
    image = Image.fromarray(frame)

    image = ImageTk.PhotoImage(image)
    image_frame.imgtk = image
    image_frame.config(image=image)

    image_frame.after(10, update_image)


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Client " + CLIENT_NAME)
    window.geometry("1280x720+300+200")

    bt_connect = tk.Button(window, text="Kết nối", activebackground="blue", bg="blue", fg="white", height=2, width=20, command=connect_to_server)
    bt_connect.place(x=20, y=8)
    bt_disconnect = tk.Button(window, text="Ngắt kết nối", activebackground="red", bg="red", fg="white", height=2, width=20, command=disconnect_from_server)
    bt_disconnect.place(x=1120, y=8)

    current_frame = np.zeros((450, 800), np.float32)
    image_frame = tk.Label(window, bg="black", width=800, height=450)
    image_frame.place(x=400, y=120)

    lb1 = tk.Label(window, text="Danh sách camera: ", font=("", 18))
    lb1.place(x=20, y=60)

    bt_reload = tk.Button(window, text="Cập nhật camera", height=1, width=15, command=reload).place(x=250, y=65)

    update_image()

    window.mainloop()

