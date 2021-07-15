# Encryption for Video Transmission in Surveillance Camera System
A project for Introduction to Information Security course IT4015

## Overview
This tool is designed as a software for management of a surveillance camera system that provide encryption for security when transferring on the internet.   

## Installation
First Download and install python (> 3.7) & pip

Start by cloning the repository:

```
git clone https://github.com/vanloc432k/Video_Ecryption
```

Create a virtual environment

```
py -m venv venv
```

Activate project's venv

```
.path\to\project\Scripts\activate
```

Installing required packages

```
python -m pip install -r requirements.txt
```

## Running
### Test on a single device
Set variables HOST_IP value in camera.py and client_app.py
```
    HOST_IP = '127.0.0.1'
``` 

Step 1: Run server on new terminal
```
    python server.py
```

Step 2: Run camera.py on new terminal
```
    # camera_mode = 0: using webcam
    # camera_mode = 1: using video
    python camera.py <Camera's Name> <camera_mode>
```

Step 3: There are 2 options: GUI app/ terminal app

3.1. GUI app:
Run client_app.py on new terminal
```
    python client_app.py <Client's Name>
```

3.2. Terminal app:
Run client_term.py
```
    python client_term.py <Client's Name>
```

Establish connect to server
```
    connect
```

Start streaming from camera
```
    start <camera_name>
```

Stop streaming from camera
```
    stop <camera_name>
```

Close all connection
```
    close
```

Exit program
```
    exit
```


**Step 2 & 3 can be repeated many times for multiple cameras streaming and multiple clients usage**

### Test on local network
Set variables HOST_IP value in camera.py and client_app.py with server's ip in the local network
```
    HOST_IP = <server_ip>
```

Repeat all step above on suitable device
+ Run server.py on server.
+ Run camera.py on camera devices or devices with video.
+ Run client_<...>.py on client devices. 
