import time
import board

# import digitalio # For use with SPI
import adafruit_bmp280


# Desc: Reads temperature, pressure, and altitude info from sensor into provided 'readings' object
def readTempPres(i2c, readings):
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
    bmp280.sea_level_pressure = 1013.25

    readings.update("temp", bmp280.temperature)
    readings.update("pres", bmp280.pressure)
    readings.update("alti", bmp280.altitude)

if __name__ == '__main__':
    i2c = board.I2C()  # uses board.SCL and board.SDA
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

    # change this to match the location's pressure (hPa) at sea level
    bmp280.sea_level_pressure = 1013.25

    while True:
        print("\nTemperature: %0.1f C" % bmp280.temperature)
        print("Pressure: %0.1f hPa" % bmp280.pressure)
        print("Altitude = %0.2f meters" % bmp280.altitude)
        time.sleep(2)