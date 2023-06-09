import os
import signal
import logging

from flask import Flask, request, jsonify
from backgroundThread import BackgroundThreadFactory

logging.basicConfig(level=logging.INFO, force=True)
currentData = {}

def create_app():
    app = Flask(__name__)
    weather_sampling_thread = BackgroundThreadFactory.create('weatherSampling', weatherData=currentData)

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
    
    @app.get('/air_quality')
    def getAirQuality():
        logging.info('Get air quality')
        return jsonify(currentData)

    return app
