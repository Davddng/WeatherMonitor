import logging
import asyncio

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
# from threadFactory import startThread
from backgroundThread import BackgroundThreadFactory
from BluetoothReader import BLEReader
from weatherData import weatherDataContainer

logging.basicConfig(level=logging.INFO, force=True)

# True if using bluetooth sensor
# False if using sensors attached to onboard GPIO
use_bluetooth = True
# def startThread(app, name):
#     weather_sampling_thread = BackgroundThreadFactory.create(name, weatherData=currentData)

#     # this condition is needed to prevent creating duplicated thread in Flask debug mode
#     if not (app.debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#         weather_sampling_thread.start()

#         original_handler = signal.getsignal(signal.SIGINT)

#         def sigint_handler(signum, frame):
#             weather_sampling_thread.stop()

#             # wait until thread is finished
#             if weather_sampling_thread.is_alive():
#                 weather_sampling_thread.join()

#             original_handler(signum, frame)

#         try:
#             signal.signal(signal.SIGINT, sigint_handler)
#         except ValueError as e:
#             logging.error(f'{e}. Continuing execution...')

class flaskApp:
    testThread = None
    testThread2 = None
    async def create_app():
        app = Flask(__name__)
        currentData = weatherDataContainer
        CORS(app)
        await BackgroundThreadFactory.startThread(app=app, name='weatherSampling', weatherData=currentData)
        if use_bluetooth:
            await BackgroundThreadFactory.startThread(app=app, name='bluetoothService', weatherData=currentData)

        @app.get('/')
        @cross_origin()
        def homePage():
            return render_template("homePage.html")
        
        @app.get('/air_quality')
        @cross_origin()
        def getAirQuality():
            logging.info('Get air quality')
            return jsonify(currentData.data)
        
        @app.route('/update_readings')
        async def updateReadings():
            logging.info('Updating air quality...')
            await BackgroundThreadFactory.startThread(app=app, name='updateWeather', weatherData=currentData)
            return jsonify({"Message": "Sensor starting... Readings will update in 30 seconds"})

        return app
