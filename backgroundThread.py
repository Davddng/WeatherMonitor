import logging
import threading
import time
import serial
import board
import schedule
import os
import signal
import asyncio

from datetime import datetime, timedelta
from abc import abstractmethod, ABC
from PMS7003 import readAirQuality, setSensorState
from BMP280 import readTempPres
from DHT22 import readTempHumid
from IMX219 import takePhoto
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
    async def startup(self):
        """
        Method that is called before the thread starts.
        Initialize all necessary resources here.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    async def shutdown(self):
        """
        Method that is called shortly after stop() method was called.
        Use it to clean up all resources before thread stops.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    async def handle(self):
        """
        Method that should contain business logic of the thread.
        Will be executed in the loop until stop() method is called.
        Must not block for a long time.
        :return: None
        """
        raise NotImplementedError()

    async def runCoroutines(self):
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
        

def updateTimestamp(readings):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    readings["timestamp"] = dt_string

class BLEReaderThread(BackgroundThread):
    bluetooth = None
    bluetoothMonitoringTask = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        BLEReaderThread.bluetooth = BLEReader(debug=True, taskQueue=kwargs["taskQueue"])

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

    async def startup(self):
        await BLEReaderThread.bluetooth.connect(name=bluetoothDeviceName)
        BLEReaderThread.bluetoothMonitoringTask = asyncio.create_task(BLEReaderThread.bluetooth.startMonitoring(characteristics=monitorCharacteristicList, onUpdate=self.updateFn))

    async def handle(self):
        while True:
            await BLEReaderThread.bluetoothMonitoringTask
        
    async def shutdown(self):
        logging.info('Bluetooth thread stopped')


async def updateSensorReadings(self):
    # Get new sensor readings from bluetooth sensors or from locally attached sensors
    if self.kwargs["bt"]:
        for characteristic in pollCharacteristicList:
            logging.info(f'Request {characteristic} update...')
            await BLEReaderThread.bluetooth.tasks.put(characteristic)
            # await self.kwargs["taskQueue"].put(characteristic)
            await asyncio.sleep(0.05)
    else:
        readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        readTempPres(self.BMP280_I2C, self.kwargs['weatherData'])
        readTempHumid(self.kwargs['weatherData'])
        logging.info(f'Weather data updated at {self.kwargs["weatherData"].data["timestamp"]}')
        
    BackgroundThreadFactory.startThread('takePicture', **self.kwargs)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    self.kwargs["weatherData"].update("timestamp", dt_string)


class weatherSampler(BackgroundThread):
    weatherSamplerTask = None
    nextSamplingDateTime = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    # Rounds to the "ceiling" of the given time delta
    def ceil_dt(self, dt, delta):
        return dt + (datetime.min - dt) % delta

    async def startup(self):
        logging.info('Weather sampling thread started')
        weatherSampler.nextSamplingDateTime = datetime.now()
        if not self.kwargs["bt"]:
            self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
            self.BMP280_I2C = board.I2C()
        # await updateSensorReadings(self)
        # logging.info(f'Initial weather data generated at {self.kwargs["weatherData"].data["timestamp"]}')
        # logging.info('Pollutant sensor needs 30 seconds to initialize, initial reading may be innaccurate')
        # schedule.every().hour.at(":00").do(self.updateWeatherData)
        # schedule.every().hour.at(":10").do(self.updateWeatherData)
        # schedule.every().hour.at(":20").do(self.updateWeatherData)
        # schedule.every().hour.at(":30").do(self.updateWeatherData)
        # schedule.every().hour.at(":40").do(self.updateWeatherData)
        # schedule.every().hour.at(":50").do(self.updateWeatherData)
        # self.updateWeatherData()
        setSensorState(False)
        
    async def shutdown(self):
        logging.info('Weather sampling thread stopped')
        setSensorState(False)

    async def handle(self):
        while True:
            now = datetime.now()
            if now > weatherSampler.nextSamplingDateTime:
                await updateSensorReadings(self)
                weatherSampler.nextSamplingDateTime = self.ceil_dt(now, timedelta(minutes=10))
                logging.info(f'Next weather sample at {weatherSampler.nextSamplingDateTime.hour}:{weatherSampler.nextSamplingDateTime.minute}')
            await asyncio.sleep(1)

class updateWeather(BackgroundThread):
    updateSensorTask = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def startup(self):
        logging.info('Sensor readings refreshing...')
        if self.kwargs["bt"]:
            updateWeather.updateSensorTask = asyncio.create_task(updateSensorReadings(self))
        else:
            self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        
    async def shutdown(self):
        logging.info('Weather update thread stopped')
        setSensorState(False)

    async def handle(self):
        await updateWeather.updateSensorTask
        logging.info(f'Weather data updated at {self.kwargs["weatherData"].data["timestamp"]}')


class takeNewPhoto(BackgroundThread):
    def startup(self) -> None:
        logging.info('Taking photo...')
        
    def shutdown(self) -> None:
        logging.info('Photo thread stopped')

    def handle(self) -> None:
        now = datetime.now()
        name = now.strftime("%Y-%m-%d-%H%M%S.jpg")
        pathToWebServer = 'static/'
        pathWithinWebServer = 'photos/'
        relativePath = pathToWebServer + pathWithinWebServer
        takePhoto(relativePath, name)
        self.kwargs["weatherData"]["photoPath"] = pathWithinWebServer + name
        logging.info('Photo saved to: ' + relativePath + name)


class BackgroundThreadFactory:
    taskQueue = asyncio.Queue()
    @staticmethod
    async def create(thread_type: str, **kwargs) -> BackgroundThread:
        kwargs["taskQueue"] = BackgroundThreadFactory.taskQueue
        async def switch(thread_type):
            if thread_type == "weatherSampling":
                return weatherSampler(**kwargs)
            if thread_type == "takePicture":
                return takeNewPhoto(**kwargs)
            elif thread_type == "updateWeather":
                return updateWeather(**kwargs)
            elif thread_type == "bluetoothService":
                return BLEReaderThread(**kwargs)
                
            raise NotImplementedError('Specified thread type is not implemented.')

        return switch(thread_type)

    async def startThread(app, name, **kwargs):
        newThread = await BackgroundThreadFactory.create(name, **kwargs)

        # this condition is needed to prevent creating duplicated thread in Flask debug mode
        if not (app.debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            newThread.start()

            original_handler = signal.getsignal(signal.SIGINT)

            def sigint_handler(signum, frame):
                newThread.stop()

                # wait until thread is finished
                if newThread.is_alive():
                    newThread.join()

                original_handler(signum, frame)

            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError as e:
                logging.error(f'{e}. Continuing execution...')
