import serial
import board
import busio
import adafruit_ssd1306
import requests
import time

from time import sleep
from PIL import Image, ImageDraw, ImageFont

class PMS:
    def __init__(self, data):
        self._pm1 = data[2] << 8 | data[3]
        self._pm25 = data[4] << 8 | data[5]
        self._pm10 = data[6] << 8 | data[7]
        self._pm1env = data[8] << 8 | data[9]
        self._pm25env = data[10] << 8 | data[11]
        self._pm10env = data[12] << 8 | data[13]
        self._pbd3 = data[14] << 8 | data[15]

        self._pbd5 = data[16] << 8 | data[17]
        self._pbd10 = data[18] << 8 | data[19]
        self._pbd25 = data[20] << 8 | data[21]
        self._pbd50 = data[22] << 8 | data[23]
        self._pbd100 = data[24] << 8 | data[25]

        self._checksum = data[26] << 8 | data[27]

    def pm1(self):
        return self._pm1

    def pm25(self):
        return self._pm25

    def pm10(self):
        return self._pm10

    def pm1env(self):
        return self._pm1env

    def pm25env(self):
        return self._pm25env

    def pm10env(self):
        return self._pm25env

    def p03(self):
        return self._pbd3

    def p05(self):
        return self._pbd5

    def p25(self):
        return self._pbd10

    def p50(self):
        return self._pbd50

    def p100(self):
        return self._pbd100

    def __str__(self):
        return "PM1.0: {0}, PM2.5: {1}, PM10: {2}".format(self.pm1(), self.pm25(), self.pm10())


def check_byte(ser, byte):
    return ord(ser.read()) == int(byte)

def pms7003(ser):
    first_byte = ser.read()
  
    #Get alignment from two starting bytes
    while not check_byte(ser, 0x42):
        continue

    if not check_byte(ser, 0x4d):
        # Missaligned return null
        return -1

    rx_data = ser.read(30)
   
    #Check length == 28
    if rx_data[1] != 28:
        return -1

    return PMS(rx_data)

def send_data(data):
    payload = {'pm1_0': data.pm1() , 'pm2_5': data.pm25(), 'pm10': data.pm10(), 'pm1_0_env': data.pm1env(), 'pm2_5_env': data.pm25env(), 'pm10_env': data.pm10env(), 'particles_03': data.p03(), 'particles_05': data.p05(), 'particles_25': data.p25(), 'particles_50': data.p50(), 'particles':data.p100()}
    
    # You will need to edit this line, or remove it all together
    r = requests.post(API_ENDPOINT_HERE, params=payload)

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # # May need to use disp = adafruit_ssd1306.SSD1306_I2C(128,64,i2c, addr=0x3d)
    # disp = adafruit_ssd1306.SSD1306_I2C(128,64,i2c)
    # disp.fill(0)
    # disp.show()

    # width = disp.width
    # height = disp.height

    # image = Image.new('1', (width, height))
    # draw = ImageDraw.Draw(image)
    
    # #Either download and place 'Arial.ttf' font in same folder, or use a different font.
    # font = ImageFont.truetype('Arial.ttf', size=12)
    
    ser = serial.Serial("/dev/ttyS0", 9600)

    counter = 0
    while True:
        data = pms7003(ser)
        if data == -1:
            continue

        counter += 1

        if counter == 60:
            send_data(data)
            counter = 0
            
        # draw.rectangle((0,0,width,height), outline=0, fill=0)
        
        # draw.text((0, 1), "PM1.0: {0}".format(data.pm1()), font=font, fill=255)
        # draw.text((0, 24), "PM2.5: {0}".format(data.pm25()), font=font, fill=255)
        # draw.text((0, 48), "PM10: {0}".format(data.pm10()), font=font, fill=255)
        
        # disp.image(image)
        # disp.show()

        print("test")

        print("PM1.0: {0}".format(data.pm1()))
        print("PM2.5: {0}".format(data.pm25()))
        print("PM10: {0}".format(data.pm10()))

        sleep(1)

if __name__ == '__main__':
    main()