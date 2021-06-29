import cv2
#import matplotlib.pyplot as plt

cam = cv2.VideoCapture(0)

while(True):
    ret, f = cam.read()

    if ret == True:
        pic = cv2.cvtColor(f, 1)

        img = cv2.resize(f, (0,0), fx=0.5, fy=0.5)
        cv2.imwrite('temp.png', img)

        cv2.imshow('Camera1', pic)
        cv2.imshow('Camera', f)
    else:
        break
    k = cv2.waitKey(1)
    if(k == 113):
        break

cam.release()
cv2.destroyAllWindows()