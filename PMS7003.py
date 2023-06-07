import serial

# Desc: Formats sensor data into dict
# Args: data - Data read from sensor
# Returns: Dictionary containing sensor values
def parseData(data):
    readings = {
        "pm1" : data[2] << 8 | data[3],
        "pm25" : data[4] << 8 | data[5],
        "pm10" : data[6] << 8 | data[7],
        "pm1env" : data[8] << 8 | data[9],
        "pm25env" : data[10] << 8 | data[11],
        "pm10env" : data[12] << 8 | data[13],
        "pbd3" : data[14] << 8 | data[15],
        "pbd5" : data[16] << 8 | data[17],
        "pbd10" : data[18] << 8 | data[19],
        "pbd25" : data[20] << 8 | data[21],
        "pbd50" : data[22] << 8 | data[23],
        "pbd100" : data[24] << 8 | data[25],
        "reserved" : data[26] << 8 | data[27],
        "checksum" : data[28] << 8 | data[29],
        "error" : 0
    }
    
    # Checksum calculation
    checksum = 0x42 + 0x4d
    for i in range(0, 27):
        checksum += data[i]
    
    if checksum != readings['checksum']:
        readings['error'] = 1
    
    return readings

# Desc: Reads sensor data
# Args: serial - Serial connection eg. serial.Serial("/dev/ttyS0", 9600)
# Returns: Dictionary containing sensor values
def readData(serial):
    
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
    return parseData(sensorData)


if __name__ == '__main__':
    data = readData(serial.Serial("/dev/ttyS0", 9600))
    print(data)

