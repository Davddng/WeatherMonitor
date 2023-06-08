import serial

from flask import Flask, request, jsonify
from PMS7003 import readData
from time import sleep

def main():
    PMS7003_SER = serial.Serial("/dev/ttyS0", 9600)

    # Web APIs
    app = Flask(__name__)

    @app.get("/air_quality")
    def getAirQuality():
        airData = readData(PMS7003_SER)
        return jsonify(airData)

    @app.post("/countries")
    def add_country():
        if request.is_json:
            country = request.get_json()
            country["id"] = _find_next_id()
            countries.append(country)
            return country, 201
        return {"error": "Request must be JSON"}, 415
    
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()