const getWeatherData = async () => {
    const response = await fetch('http://192.168.1.178:5000/air_quality');
    const weatherResponse = await response.json();

    console.log(weatherResponse)
    document.getElementById("pm1.0").innerHTML = weatherResponse['pm1'];
    document.getElementById("pm2.5").innerHTML = weatherResponse['pm25'];
    document.getElementById("pm10").innerHTML = weatherResponse['pm10']; 
    // temperature in celcius
    temp = weatherResponse['temp'];
    document.getElementById("temp").innerHTML = temp.toFixed(1) + " °C, " + ((temp * 9/5) + 32) + " °F"; 
    // pressure in hPa, same as millibar
    pres = weatherResponse['pres'] 
    document.getElementById("pres").innerHTML = (pres/10).toFixed(1) + " kPa, " + pres.toFixed(1) + " Millibars"; 
    document.getElementById("HeaderText").innerHTML = "Weather Data Sampled At " + weatherResponse['timestamp'];
  }

getWeatherData()
setInterval(getWeatherData, 30000);