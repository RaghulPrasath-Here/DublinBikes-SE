

import sqlalchemy as sqla
from sqlalchemy import create_engine, text
import traceback
import json
import requests

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from JCDAPI import dbinfo as db
from datetime import datetime

############################# CONNECT TO THE DATABASE #######################################

connection_string = f"mysql+pymysql://{db.USER}:{db.PASSWORD}@{db.URI}:{db.PORT}/{db.DB}"
engine = create_engine(connection_string, echo=True)


############################ FUNCTION TO INSERT HOURLY WEATHER #############################
def get_weather_category(weather_id):
    """Classify weather conditions into categories based on weather_id"""
    if weather_id is None:
        return "Unknown"
    elif 200 <= weather_id < 300:
        return "Thunderstorm"
    elif 300 <= weather_id < 400:
        return "Drizzle"
    elif 500 <= weather_id < 600:
        return "Rainy"
    elif 600 <= weather_id < 700:
        return "Snowy"
    elif 700 <= weather_id < 800:
        return "Atmosphere"
    elif weather_id == 800:
        return "Clear"
    elif 801 <= weather_id < 810:
        return "Cloudy"
    else:
        return "Unknown"

def hourlyWeather_to_db(text_data, in_engine):
    ''' Inserts and updates hourly weather data in the hourlyWeather table '''

    try:
        conditions = json.loads(text_data)  # Parse JSON response
        print("Parsed Hourly Weather JSON:", conditions)  # Debugging output

        if "list" not in conditions:
            raise KeyError("Missing 'list' key in API response")

        hourly_data = conditions["list"]  # Extract hourly forecast list

        insert_condition = text("""
            INSERT INTO hourlyWeather (dt, temp, feels_like, humidity, pressure, wind_speed, weather_id, weather_category, weather_description, rain_1h, snow_1h, recorded_at)
            VALUES (:dt, :temp, :feels_like, :humidity, :pressure, :wind_speed, :weather_id, :weather_category, :weather_description, :rain_1h, :snow_1h, NOW())
            ON DUPLICATE KEY UPDATE
            temp = VALUES(temp),
            feels_like = VALUES(feels_like),
            humidity = VALUES(humidity),
            pressure = VALUES(pressure),
            wind_speed = VALUES(wind_speed),
            weather_id = VALUES(weather_id),
            weather_category = VALUES(weather_category),
            weather_description = VALUES(weather_description),
            rain_1h = VALUES(rain_1h),
            snow_1h = VALUES(snow_1h),
            recorded_at = NOW();
        """)

        with in_engine.connect() as connection:
            for hour in hourly_data:
                weather_id = hour["weather"][0].get("id") if "weather" in hour else None
                vals = {
                    "dt": datetime.utcfromtimestamp(hour["dt"]).strftime('%Y-%m-%d %H:%M:%S'),
                    "temp": hour["main"].get("temp"),
                    "feels_like": hour["main"].get("feels_like"),
                    "humidity": hour["main"].get("humidity"),
                    "pressure": hour["main"].get("pressure"),
                    "wind_speed": hour["wind"].get("speed"),
                    "weather_id": weather_id,
                    "weather_category": get_weather_category(weather_id),  # Categorized weather
                    "weather_description": hour["weather"][0].get("description") if "weather" in hour else None,
                    "rain_1h": hour.get("rain", {}).get("1h", None),
                    "snow_1h": hour.get("snow", {}).get("1h", None),
                }
                connection.execute(insert_condition, vals)

            connection.commit()

        print("✅ Hourly weather data successfully inserted into DB!")

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
    except KeyError as e:
        print(f"Missing expected key in API response: {e}")
    except Exception as e:
        print("Database Insertion Error:", traceback.format_exc())


############################# FETCH DATA FROM OPEN WEATHER API #############################

try:
    # Request data from OW API
    responseHourly = requests.get(f"{db.HOURLY_OWRUI}")

    
  
    hourlyWeather_to_db(responseHourly.text, engine)
    
except Exception as e:
    print("Error:", traceback.format_exc())




