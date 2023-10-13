import logging
import threading
import time
import serial
import board
import schedule
import asyncio

from datetime import datetime
from abc import abstractmethod, ABC
from PMS7003 import readAirQuality, setSensorState
from BMP280 import readTempPres
from DHT22 import readTempHumid
from BluetoothReader import BLEReader

# Name or address of bluetooth sensor to connect 
bluetoothDeviceName = "28:CD:C1:0D:5C:C0"
monitorCharacteristicList = ["Temperature", "Humidity", "Pressure", "PM1 Concentration", "PM2.5", "PM10"]
pollCharacteristicList = ["Temperature", "Humidity", "Pressure", "PM1 Concentration"]

class BackgroundThread(threading.Thread, ABC):
    def __init__(self, **kwargs):
        super().__init__()
        self._stop_event = threading.Event()
        self.kwargs = kwargs

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()

    @abstractmethod
    async def startup(self) -> None:
        """
        Method that is called before the thread starts.
        Initialize all necessary resources here.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Method that is called shortly after stop() method was called.
        Use it to clean up all resources before thread stops.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    async def handle(self) -> None:
        """
        Method that should contain business logic of the thread.
        Will be executed in the loop until stop() method is called.
        Must not block for a long time.
        :return: None
        """
        raise NotImplementedError()

    async def runCoroutines(self) -> None:
        """
        This method will be executed in a separate thread
        when start() method is called.
        :return: None
        """
        await self.startup()
        await self.handle()
        await self.shutdown()
        
    def run(self) -> None:
        asyncio.run(self.runCoroutines())
        


class BLEReaderThread(BackgroundThread):
    BLEReader = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        BLEReaderThread.BLEReader = BLEReader(debug=True, taskQueue=kwargs["taskQueue"])

    def updateFn(self, label, val):
        logging.info(f'{label} was updated to: {val}')
        if label == "Temperature":
            self.kwargs["weatherData"].update("temp", val)
        elif label == "Humidity":
            self.kwargs["weatherData"].update("humid", val)
        elif label == "Pressure":
            self.kwargs["weatherData"].update("pres", val)
        elif label == "PM1 Concentration":
            self.kwargs["weatherData"].update("pm1", val)
        elif label == "PM2.5":
            self.kwargs["weatherData"].update("pm25", val)
        elif label == "PM10":
            self.kwargs["weatherData"].update("pm10", val)

    async def startup(self) -> None:
        await BLEReaderThread.BLEReader.connect(name=bluetoothDeviceName)

    async def handle(self) -> None:
        BLEReaderThread.BLEReader.startMonitoring(characteristics=monitorCharacteristicList, onUpdate=self.updateFn)
    
    def shutdown(self) -> None:
        logging.info('Bluetooth thread stopped')


async def updateSensorReadings(self):
    # Get new sensor readings from bluetooth sensors or from locally attached sensors
    self.updateTimestamp()
    if self.kwargs["bt"]:
        for characteristic in pollCharacteristicList:
            logging.info(f'Updating {characteristic}...')
            await self.kwargs["taskQueue"].put(characteristic)
            await asyncio.sleep(0.05)
    else:
        readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        readTempPres(self.BMP280_I2C, self.kwargs['weatherData'])
        readTempHumid(self.kwargs['weatherData'])

class weatherSampler(BackgroundThread):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def updateTimestamp(self):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.kwargs["weatherData"].update("timestamp", dt_string)
        
    async def updateWeatherData(self):
        await updateSensorReadings(self)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"].data["timestamp"]}')

    async def startup(self) -> None:
        logging.info('Weather sampling thread started')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        self.BMP280_I2C = board.I2C()
        await updateSensorReadings(self)
        # self.kwargs["weatherData"].update("timestamp", "test")
        logging.info(f'Initial weather data generated at {self.kwargs["weatherData"].data["timestamp"]}')
        logging.info('Pollutant sensor needs 30 seconds to initialize, initial reading may be innaccurate')
        schedule.every().hour.at(":00").do(self.updateWeatherData)
        schedule.every().hour.at(":10").do(self.updateWeatherData)
        schedule.every().hour.at(":20").do(self.updateWeatherData)
        schedule.every().hour.at(":30").do(self.updateWeatherData)
        schedule.every().hour.at(":40").do(self.updateWeatherData)
        schedule.every().hour.at(":50").do(self.updateWeatherData)
        self.updateWeatherData()
        setSensorState(False)
        
    def shutdown(self) -> None:
        logging.info('Weather sampling thread stopped')
        setSensorState(False)

    def handle(self) -> None:
        while not self._stopped():
            schedule.run_pending()
            time.sleep(1)


class updateWeather(BackgroundThread):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def updateWeatherData(self):
        await updateSensorReadings(self)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"].data["timestamp"]}')
        
    def startup(self) -> None:
        logging.info('Sensor readings refreshing...')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        
    def shutdown(self) -> None:
        logging.info('Weather update thread stopped')
        setSensorState(False)

    def handle(self) -> None:
        self.updateWeatherData()


class BackgroundThreadFactory:
    taskQueue = asyncio.Queue()
    @staticmethod
    async def create(thread_type: str, **kwargs) -> BackgroundThread:
        kwargs["taskQueue"] = BackgroundThreadFactory.taskQueue
        async def switch(thread_type):
            if thread_type == "weatherSampling":
                return weatherSampler(**kwargs)
            elif thread_type == "updateWeather":
                return updateWeather(**kwargs)
            elif thread_type == "bluetoothService":
                return BLEReaderThread(**kwargs)
                
            raise NotImplementedError('Specified thread type is not implemented.')

        return await switch(thread_type)
