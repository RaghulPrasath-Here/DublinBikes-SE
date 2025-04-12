const time = new Date().getHours();
let timeOfTheDay;
if (time >= 6 && time < 19) {
    timeOfTheDay = "Day";
} else {
    timeOfTheDay = "Night";
}

// Fetch weather from Flask API
fetch('/weather')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const temperature = data.temperature;
        const condition = data.condition;  // e.g. "Rain", "Clear", "Broken Clouds"
        let icon = '';

        // Normalize the condition string
        const normalized = condition.toLowerCase();
        const isDay = timeOfTheDay === "Day";

        if (normalized.includes('rain') && isDay) {
            icon = 'static/images/rain_day.png';
        } else if (normalized.includes('rain') && !isDay) {
            icon = 'static/images/rain_night.png';
        } else if (normalized.includes('atmosphere') && isDay) {
            icon = 'static/images/atmosphere_day.png';
        } else if (normalized.includes('atmosphere') && !isDay) {
            icon = 'static/images/atmosphere_night.png';
        } else if (normalized.includes('clear') && isDay) {
            icon = 'static/images/clear_day.png';
        } else if (normalized.includes('clear') && !isDay) {
            icon = 'static/images/clear_night.png';
        } else if (normalized.includes('cloud') && isDay) {
            icon = 'static/images/clouds_day.png';
        } else if (normalized.includes('cloud') && !isDay) {
            icon = 'static/images/clouds_night.png';
        } else if (normalized.includes('drizzle')) {
            icon = 'static/images/drizzle.png';
        } else if (normalized.includes('snow')) {
            icon = 'static/images/snow.png';
        } else if (normalized.includes('thunderstorm') && isDay) {
            icon = 'static/images/thunderstorm_day.png';
        } else if (normalized.includes('thunderstorm') && !isDay) {
            icon = 'static/images/thunderstorm_night.png';
        }

        document.getElementById("temperature").innerHTML = temperature + "°C";
        document.getElementById("weather-condition").innerHTML = condition;
        document.getElementById("weather-icon").src = icon;
    })
    .catch(error => {
        console.error('Error fetching weather:', error);
    });
