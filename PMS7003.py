import serial
import RPi.GPIO as GPIO

# Desc: Updates sensor data on readings variable
# Args: data - Data read from sensor
def parseData(data, readings):
    readings["pm1"] = data[2] << 8 | data[3]
    readings["pm25"] = data[4] << 8 | data[5]
    readings["pm10"] = data[6] << 8 | data[7]
    readings["pm1env"] = data[8] << 8 | data[9]
    readings["pm25env"] = data[10] << 8 | data[11]
    readings["pm10env"] = data[12] << 8 | data[13]
    readings["pbd3"] = data[14] << 8 | data[15]
    readings["pbd5"] = data[16] << 8 | data[17]
    readings["pbd10"] = data[18] << 8 | data[19]
    readings["pbd25"] = data[20] << 8 | data[21]
    readings["pbd50"] = data[22] << 8 | data[23]
    readings["pbd100"] = data[24] << 8 | data[25]
    readings["reserved"] = data[26] << 8 | data[27]
    readings["checksum"] = data[28] << 8 | data[29]
    readings["error"] = 0
    
    # Checksum calculation
    checksum = 0x42 + 0x4d
    for i in range(0, 27):
        checksum += data[i]
    
    if checksum != readings['checksum']:
        readings['error'] = 1
    

# Desc: Turn sensor on or off
# Args: state - true = on, false = off
def setSensorState(state): 
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18,GPIO.OUT)

    if state:
        GPIO.output(18,GPIO.HIGH)
    else:
        GPIO.output(18,GPIO.LOW)


# Desc: Reads sensor data into the provided 'readings' variable
# Args: serial - Serial connection eg. serial.Serial("/dev/ttyS0", 9600)
def readData(serial, readings):
    
    serial.reset_input_buffer()
    
#     first two bytes returned by sensor are 0x42 followed by 0x4d. Next 30 bytes are data
    tryCounter = -1
    while True:
        tryCounter += 1
        if ord(serial.read()) == 0x42:
            if ord(serial.read()) == 0x4d:
                break
        else:
            if tryCounter <= 128:
                continue
            else:
                return -1

    sensorData = serial.read(30)
    parseData(sensorData, readings)


if __name__ == '__main__':
    readings = {}
    readData(serial.Serial("/dev/ttyS0", 9600), readings)
    print(readings)

