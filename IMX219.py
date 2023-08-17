import time
import os
import logging

from picamera2 import Picamera2
from datetime import datetime


def takePhoto(path):
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    abs_file_path = os.path.join(script_dir, path)

    camera = Picamera2()
    picture_config = camera.create_still_configuration()
    camera.configure(picture_config)
    
    camera.start()
    time.sleep(5)
    print(abs_file_path)
    camera.capture_file(abs_file_path)
    camera.close()

if __name__ == '__main__':
    now = datetime.now()
    path = now.strftime("%Y%m%d-%H%M%S")
    takePhoto(path)
    logging.info('Photo saved to: ' + path)