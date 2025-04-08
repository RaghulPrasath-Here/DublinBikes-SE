import sqlalchemy as sqla
from sqlalchemy import create_engine, text
import traceback
import json
import requests
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from JCDAPI import dbinfo as db
from datetime import datetime

############################# CONNECT TO THE DATABASE #######################################

connection_string = f"mysql+pymysql://{db.USER}:{db.PASSWORD}@{db.URI}:{db.PORT}/{db.DB}"
engine = create_engine(connection_string, echo=True)

############################ FUNCTION TO INSERT CURRENT WEATHER #############################
import traceback
from sqlalchemy import text

def currentWeather_to_db(text_data, in_engine):
    ''' Inserts and updates current weather meta data in the currentWeather table'''

    try:
        conditions = json.loads(text_data)
        print("Parsed JSON:", conditions)  # Debugging output

        # Convert UNIX timestamps to MySQL DATETIME format
        vals = {
            "dt": datetime.utcfromtimestamp(conditions.get("dt")).strftime('%Y-%m-%d %H:%M:%S') if conditions.get("dt") else None,
            "temp": conditions["main"].get("temp"),
            "feels_like": conditions["main"].get("feels_like"),
            "humidity": conditions["main"].get("humidity"),
            "pressure": conditions["main"].get("pressure"),
            "wind_speed": conditions["wind"].get("speed"),
            "wind_gust": conditions["wind"].get("gust", None),
            "weather_id": conditions["weather"][0].get("id") if conditions.get("weather") else None,
            "weather_description": conditions["weather"][0].get("description") if conditions.get("weather") else None,
            "rain_1h": conditions["rain"].get("1h", None) if "rain" in conditions else None,
            "snow_1h": conditions["snow"].get("1h", None) if "snow" in conditions else None
        }

        insert_condition = text("""
            INSERT INTO currentWeather (dt, temp, feels_like, humidity, pressure, wind_speed, wind_gust, weather_id, weather_description, rain_1h, snow_1h)
            VALUES (:dt, :temp, :feels_like, :humidity, :pressure, :wind_speed, :wind_gust, :weather_id, :weather_description, :rain_1h, :snow_1h)
            ON DUPLICATE KEY UPDATE
            temp = VALUES(temp),
            feels_like = VALUES(feels_like),
            humidity = VALUES(humidity),
            pressure = VALUES(pressure),
            wind_speed = VALUES(wind_speed),
            wind_gust = VALUES(wind_gust),
            weather_id = VALUES(weather_id),
            weather_description = VALUES(weather_description),
            rain_1h = VALUES(rain_1h),
            snow_1h = VALUES(snow_1h);
        """)

        # Insert into DB
        with in_engine.connect() as connection:
            connection.execute(insert_condition, vals)
            connection.commit()

        print("Data successfully inserted into DB!")

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
    except KeyError as e:
        print(f"Missing expected key in API response: {e}")
    except Exception as e:
        print("Database Insertion Error:", traceback.format_exc())


############################# FETCH DATA FROM OPEN WEATHER API #############################

try:
    # Request data from OW API
    responseCurrent = requests.get(f"{db.CURRENT_OWURI}")
    
    # Insert various time ranges into the DB
    currentWeather_to_db(responseCurrent.text, engine)

except Exception as e:
    print("Error:", traceback.format_exc())
