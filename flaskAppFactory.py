import os
import signal
import logging
import asyncio

from threading import Lock
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
from backgroundThread import BackgroundThreadFactory
from BluetoothReader import BLEReader

logging.basicConfig(level=logging.INFO, force=True)

# True if using bluetooth sensor
# False if using sensors attached to onboard GPIO
use_bluetooth = True
# currentData = {}

class weatherDataContainer():
    data = {}
    busy = Lock()

    def update(self, key, value):
        weatherDataContainer.busy.acquire()
        weatherDataContainer.data[key] = value
        weatherDataContainer.busy.release()

def startThread(app, name):
    newThread = BackgroundThreadFactory.create(name, weatherData=weatherDataContainer(), bt=use_bluetooth)

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


def create_app():
    app = Flask(__name__)
    currentData = weatherDataContainer()
    CORS(app)
    startThread(app, 'weatherSampling')
    if use_bluetooth:
        startThread(app, 'bluetoothService')

    @app.get('/')
    @cross_origin()
    def homePage():
        return render_template("homePage.html")
    
    @app.get('/air_quality')
    @cross_origin()
    def getAirQuality():
        logging.info('Get air quality')
        return jsonify(currentData.data)
    
    @app.get('/update_readings')
    @cross_origin()
    def updateReadings():
        logging.info('Updating air quality...')
        startThread(app, 'updateWeather')
        return jsonify({"Message": "Sensor starting... Readings will update in 30 seconds"})

    return app
