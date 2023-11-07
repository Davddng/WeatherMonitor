import serial
import RPi.GPIO as GPIO
import time

from weatherData import weatherDataContainer

# Desc: Updates sensor data on readings variable
# Args: data - Data read from sensor
def parseData(data, readings):
    readings.update("pm1", data[2] << 8 | data[3])
    readings.update("pm25", data[4] << 8 | data[5])
    readings.update("pm10", data[6] << 8 | data[7])
    readings.update("pm1env", data[8] << 8 | data[9])
    readings.update("pm25env", data[10] << 8 | data[11])
    readings.update("pm10env", data[12] << 8 | data[13])
    readings.update("pbd3", data[14] << 8 | data[15])
    readings.update("pbd5", data[16] << 8 | data[17])
    readings.update("pbd10", data[18] << 8 | data[19])
    readings.update("pbd25", data[20] << 8 | data[21])
    readings.update("pbd50", data[22] << 8 | data[23])
    readings.update("pbd100", data[24] << 8 | data[25])
    readings.update("reserved", data[26] << 8 | data[27])
    readings.update("checksum", data[28] << 8 | data[29])
    readings.update("error", 0)

    # Checksum calculation
    checksum = 0x42 + 0x4d
    for i in range(0, 27):
        checksum += data[i]
    
    if checksum != readings.data['checksum']:
        readings.update('error', 1)
    

# Desc: Turn sensor on or off
# Args: state - true = on, false = off
def setSensorState(state): 
    print("sensor: ", state)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18,GPIO.OUT)

    if state:
        GPIO.output(18,GPIO.HIGH)
    else:
        GPIO.output(18,GPIO.LOW)


# Desc: Turns on sensor, waits 30 seconds for startup, then reads sensor data into the provided 'readings' object
# Args: serial - Serial connection eg. serial.Serial("/dev/ttyS0", 9600), readings - Object to put readings into, warmUpTime - Time to wait for sensor to wake from sleep
def readAirQuality(serial, readings, warmUpTime):
    setSensorState(True)
    time.sleep(warmUpTime)
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
    setSensorState(False)


if __name__ == '__main__':
    readings = weatherDataContainer()
    readAirQuality(serial.Serial("/dev/ttyS0", 9600), readings)
    print(readings)

