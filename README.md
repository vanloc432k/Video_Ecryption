# Video_Ecryption
Video_Ecryption

**Operation Note: (terminal script)**
Each step runs on a new terminal
Step 1: python server.py
Step 2: python camera.py <camera_name> <mode>
	0: webcam mode
	1: test video mode
Step 3: python client.py <client_name> 
Step 4: enter command in client cmd:
	'connect' : establish connect to server
	'start <camera_name>': get data from camera
	'exit': exit client program 