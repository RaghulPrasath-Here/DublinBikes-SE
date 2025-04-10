from flask import Flask, g
import os
import requests
from dotenv import load_dotenv
load_dotenv()

JCKEY = os.getenv("JCKEY")
CONTRACT = "dublin"
STATIONS_URI = F"https://api.jcdecaux.com/vls/v1/stations?contract={CONTRACT}&apiKey={JCKEY}"


def get_stations():
    response = requests.get(STATIONS_URI)
    
    return response.json()