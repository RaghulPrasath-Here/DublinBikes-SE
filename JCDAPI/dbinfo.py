from dotenv import load_dotenv
import os
load_dotenv()

# JCDecaux API Credentials
JCKEY = os.getenv("JCKEY")
NAME = "dublin"
STATIONS_URI = "https://api.jcdecaux.com/vls/v1/stations"