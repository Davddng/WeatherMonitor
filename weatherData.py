from threading import Lock

class weatherDataContainer():
    data = {}
    busy = Lock()

    def update(key, value):
        weatherDataContainer.busy.acquire()
        weatherDataContainer.data[key] = value
        weatherDataContainer.busy.release()