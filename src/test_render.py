import cv2
import numpy as np
import threading

count = 0

def stream_video(index):
    vid = cv2.VideoCapture('video/about.mp4')
    frame_counter = 0
    while vid.isOpened():
        img, frame = vid.read()

        frame_counter += 1
        # If the last frame is reached, reset the capture and the frame_counter
        if frame_counter == vid.get(cv2.CAP_PROP_FRAME_COUNT):
            frame_counter = 0  # Or whatever as long as it is the same as next line
            vid.set(cv2.CAP_PROP_POS_FRAMES, 0)

        window_name = 'Test'
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)
        if key == 27:
            cv2.destroyWindow(window_name)
            break


while True:
    if input('Enter command: ') == 'reset':
        count += 1
        thread = threading.Thread(target=stream_video, args=(count,))
        thread.start()
