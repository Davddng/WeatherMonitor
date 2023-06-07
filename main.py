import serial

from PMS7003 import readData
from time import sleep

def main():
    ser = serial.Serial("/dev/ttyS0", 9600)

    counter = 0
    while True:
        data = readData(ser)
        if counter == 5:
            break

        counter += 1
        print("Reading {0}".format(counter))
        print("PM1.0: {0}".format(data['pm1']))
        print("PM2.5: {0}".format(data['pm25']))
        print("PM10: {0}".format(data['pm10']))

        sleep(1)

if __name__ == '__main__':
    main()