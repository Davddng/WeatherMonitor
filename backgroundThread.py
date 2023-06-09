import logging
import threading
import time
import serial
import schedule

from abc import abstractmethod, ABC
from PMS7003 import readData


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
        while not self._stopped():
            self.handle()
            time.sleep(1)
        self.shutdown()


class weatherSampler(BackgroundThread):
    def updateWeatherData(self):
        self.weatherData = readData(self.PMS7003_SER, self.kwargs['weatherData'])

    def startup(self) -> None:
        logging.info('Weather sampling thread started')
        self.PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)
        self.updateWeatherData(self)
        schedule.every(15).seconds.do(self.updateWeatherData(self))
        # TODO: Implement device startup
        

    def shutdown(self) -> None:
        logging.info('Weather sampling thread stopped')
        # TODO: Implement device shutdown


    def handle(self) -> None:
        schedule.run_pending()


class BackgroundThreadFactory:
    @staticmethod
    def create(thread_type: str, **kwargs) -> BackgroundThread:
        if thread_type == 'weatherSampling':
            return weatherSampler(**kwargs)

        # if thread_type == 'some_other_type':
        #     return SomeOtherThread()

        raise NotImplementedError('Specified thread type is not implemented.')
