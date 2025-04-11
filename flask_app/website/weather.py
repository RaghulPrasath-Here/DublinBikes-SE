from flask import Flask, g
import os
import requests
from dotenv import load_dotenv
load_dotenv()


# OPEN WEATHER API Credentials
LAT = 53.3498
LONG = -6.2603
OWKEY = os.getenv("OWKEY")
CURRENT_OWURI = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LONG}&appid={OWKEY}&units=metric"
HOURLY_OWRUI = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={LAT}&lon={LONG}&appid={OWKEY}&units=metric"
DAILY_OWURI = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={LAT}&lon={LONG}&cnt=7&appid={OWKEY}&units=metric"



def current_weather_from_coordinates(LAT,LONG):
    temperature = 0
    main_weather = ""
    
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LONG}&appid={OWKEY}&units=metric")
    data = response.json()
    temperature = round(data['main']['temp'])
    main_weather = data["weather"][0]["main"]
    
    return {"temperature":temperature, "condition": main_weather}