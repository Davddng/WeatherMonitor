import os
import signal
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from backgroundThread import BackgroundThreadFactory
from PMS7003 import readData

logging.basicConfig(level=logging.INFO, force=True)
currentData = {}

def startThread(app, name):
    weather_sampling_thread = BackgroundThreadFactory.create(name, weatherData=currentData)

    # this condition is needed to prevent creating duplicated thread in Flask debug mode
    if not (app.debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
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


def create_app():
    app = Flask(__name__)
    CORS(app)
    startThread(app, 'weatherSampling')

    @app.get('/')
    @cross_origin()
    def homePage():
        return render_template("homePage.html")
    
    @app.get('/air_quality')
    @cross_origin()
    def getAirQuality():
        logging.info('Get air quality')
        return jsonify(currentData)
    
    @app.get('/update_readings')
    @cross_origin()
    def updateReadings():
        logging.info('Updating air quality...')
        startThread(app, 'updateWeather')
        return jsonify({"Message": "Sensor starting... Readings will update in 30 seconds"})

    return app
