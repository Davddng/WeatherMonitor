import logging
import threading
import time
import serial
import board
import schedule
import os
import signal

from datetime import datetime
# from threadFactory import startThread
from abc import abstractmethod, ABC
from PMS7003 import readAirQuality, setSensorState
from BMP280 import readTempPres
from DHT22 import readTempHumid
from IMX219 import takePhoto


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
    def startup(self) -> None:
        """
        Method that is called before the thread starts.
        Initialize all necessary resources here.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def shutdown(self) -> None:
        """
        Method that is called shortly after stop() method was called.
        Use it to clean up all resources before thread stops.
        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def handle(self) -> None:
        """
        Method that should contain business logic of the thread.
        Will be executed in the loop until stop() method is called.
        Must not block for a long time.
        :return: None
        """
        raise NotImplementedError()

    def run(self) -> None:
        """
        This method will be executed in a separate thread
        when start() method is called.
        :return: None
        """
        self.startup()
        self.handle()
        self.shutdown()

def updateTimestamp(readings):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    readings["timestamp"] = dt_string

def updateSensorReadings(self):
    readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 30)
    readTempPres(self.BMP280_I2C, self.kwargs['weatherData'])
    readTempHumid(self.kwargs['weatherData'])
    updateTimestamp(self.kwargs['weatherData'])

class weatherSampler(BackgroundThread):        
    def updateWeatherData(self):
        # readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        # readTempPres(self.BMP280_I2C, self.kwargs['weatherData'])
        # readTempHumid(self.kwargs['weatherData'])
        # self.updateTimestamp()
        BackgroundThreadFactory.startThread('takePicture', **self.kwargs)
        updateSensorReadings(self)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"]["timestamp"]}')

    def startup(self) -> None:
        logging.info('Weather sampling thread started')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        self.BMP280_I2C = board.I2C()
        # readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 0)
        # readTempPres(self.BMP280_I2C, self.kwargs['weatherData'])
        # self.updateTimestamp()
        updateSensorReadings(self)

        logging.info(f'Initial weather data generated at {self.kwargs["weatherData"]["timestamp"]}')
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
    def updateWeatherData(self):
        # readAirQuality(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        updateSensorReadings(self)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"]["timestamp"]}')
        
    def startup(self) -> None:
        logging.info('Sensor readings refreshing...')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        
    def shutdown(self) -> None:
        logging.info('Weather update thread stopped')
        setSensorState(False)

    def handle(self) -> None:
        self.updateWeatherData()

class takeNewPhoto(BackgroundThread):
    def startup(self) -> None:
        logging.info('Taking photo...')
        
    def shutdown(self) -> None:
        logging.info('Photo thread stopped')

    def handle(self) -> None:
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        time = now.strftime("%H-%M")
        path = year + '/' + month + '/' + day + '/' + time + '.jpg'
        takePhoto(path)
        logging.info('Photo saved to: ' + path)


class BackgroundThreadFactory:
    @staticmethod
    def create(thread_type: str, **kwargs) -> BackgroundThread:
        def switch(thread_type):
            if thread_type == "weatherSampling":
                return weatherSampler(**kwargs)
            if thread_type == "takePicture":
                return takeNewPhoto(**kwargs)
            elif thread_type == "updateWeather":
                return updateWeather(**kwargs)
                
            raise NotImplementedError('Specified thread type is not implemented.')

        return switch(thread_type)

    @staticmethod
    def startThread(name, **kwargs):
        weather_sampling_thread = BackgroundThreadFactory.create(name, **kwargs)

        # this condition is needed to prevent creating duplicated thread in Flask debug mode
        if not (kwargs["app"].debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            weather_sampling_thread.start()

            original_handler = signal.getsignal(signal.SIGINT)

            def sigint_handler(signum, frame):
                weather_sampling_thread.stop()

                # wait until thread is finished
                if weather_sampling_thread.is_alive():
                    weather_sampling_thread.join()

                original_handler(signum, frame)

            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError as e:
                logging.error(f'{e}. Continuing execution...')
