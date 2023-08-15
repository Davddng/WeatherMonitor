import Adafruit_DHT as dht
from time import sleep
#Set DATA pin
DHT = 4

# Desc: Reads temperature and humidity info from sensor into provided 'readings' object
def readTempHumid(readings):
    h,t = dht.read_retry(dht.DHT22, DHT)
    readings["humid"] = h
    readings["temp2"] = t

if __name__ == '__main__':
    while True:
        #Read Temp and Hum from DHT22
        h,t = dht.read_retry(dht.DHT22, DHT)
        #Print Temperature and Humidity on Shell window
        print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(t,h))
        print(h + " " + t)
        sleep(5) #Wait 5 seconds and read again