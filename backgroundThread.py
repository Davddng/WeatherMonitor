import logging
import threading
import time
import serial
import schedule

from abc import abstractmethod, ABC
from PMS7003 import readData, setSensorState


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


class weatherSampler(BackgroundThread):
    def updateWeatherData(self):
        readData(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"]["timestamp"]}')

    def startup(self) -> None:
        logging.info('Weather sampling thread started')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        readData(self.PMS7003_SER, self.kwargs['weatherData'], 0)
        logging.info(f'Initial weather data generated at {self.kwargs["weatherData"]["timestamp"]}')
        logging.info('Sensor needs 30 seconds to initialize, initial reading may be innaccurate')
        schedule.every(10).minutes.do(self.updateWeatherData)
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
        readData(self.PMS7003_SER, self.kwargs['weatherData'], 30)
        logging.info(f'Weather data updated at {self.kwargs["weatherData"]["timestamp"]}')
        
    def startup(self) -> None:
        logging.info('Sensor readings refreshing...')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        
    def shutdown(self) -> None:
        logging.info('Weather update thread stopped')
        setSensorState(False)

    def handle(self) -> None:
        self.updateWeatherData()


class BackgroundThreadFactory:
    @staticmethod
    def create(thread_type: str, **kwargs) -> BackgroundThread:
        if thread_type == 'weatherSampling':
            return weatherSampler(**kwargs)
        
        if thread_type == 'updateWeather':
            return updateWeather(**kwargs)

        # if thread_type == 'some_other_type':
        #     return SomeOtherThread()

        raise NotImplementedError('Specified thread type is not implemented.')
