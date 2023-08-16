from picamera import PiCamera
import time

def takePhoto(path):
    camera = PiCamera()
    time.sleep(5)
    camera.capture(path)
    # print("Done.")

if __name__ == '__main__':
    takePhoto("test.jpg")