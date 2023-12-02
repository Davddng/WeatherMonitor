const getWeatherData = async () => {
    const response = await fetch('http://' + window.location.host + '/air_quality');
    const weatherResponse = await response.json();

    console.log(weatherResponse)
    document.getElementById("pm1.0").innerHTML = weatherResponse['pm1'];
    document.getElementById("pm2.5").innerHTML = weatherResponse['pm25'];
    document.getElementById("pm10").innerHTML = weatherResponse['pm10']; 
    // temperature in celcius
    temp = weatherResponse['temp'];
    document.getElementById("temp").innerHTML = temp.toFixed(2) + " °C<br>" + ((temp * 9/5) + 32).toFixed(1) + " °F"; 
    // pressure in hPa, same as millibar
    pres = weatherResponse['pres']
    pressureText = pres.toFixed(2) + " kPa<br>";
    pressureText += (pres*10).toFixed(1) + " Millibars<br>";
    pressureText += (pres*0.2953).toFixed(2) + " inHg";

    document.getElementById("pres").innerHTML = pressureText; 
    // relative humidity
    humid = weatherResponse['humid'];
    document.getElementById("humid").innerHTML = humid.toFixed(1) + "%"; 
    
    // image path
    imgPath = weatherResponse['photoPath'];
    img = document.getElementById("headerImage");
    img.src = "static/" + imgPath;

    
    document.getElementById("HeaderText").innerHTML = "Weather Data Sampled At " + weatherResponse['timestamp'];
  }

getWeatherData()
setInterval(getWeatherData, 30000);
