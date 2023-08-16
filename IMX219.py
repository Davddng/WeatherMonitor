from picamera import PiCamera
import time
import os

def takePhoto(path):
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    abs_file_path = os.path.join(script_dir, path)

    camera = PiCamera()
    time.sleep(5)
    camera.capture(abs_file_path)
    # print("Done.")

if __name__ == '__main__':
    takePhoto("test.jpg")