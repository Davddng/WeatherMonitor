import Adafruit_DHT as dht
from time import sleep
from weatherData import weatherDataContainer
#Set DATA pin
DHT = 4

# Desc: Reads temperature and humidity info from sensor into provided 'readings' object
def readTempHumid(readings):
    h,t = dht.read_retry(dht.DHT22, DHT)
    readings.update("humid", h)
    readings.update("temp2", t)

if __name__ == '__main__':
    while True:
        #Read Temp and Hum from DHT22
        h,t = dht.read_retry(dht.DHT22, DHT)
        #Print Temperature and Humidity on Shell window
        test = weatherDataContainer()
        readTempHumid(test)
        print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(test.data['temp2'],test.data['humid']))
        sleep(5) #Wait 5 seconds and read again
