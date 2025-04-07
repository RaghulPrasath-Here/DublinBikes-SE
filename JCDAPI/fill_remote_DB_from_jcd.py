import json
import requests
import traceback
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from JCDAPI import dbinfo as db

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from JCDAPI.create_db_programs.create_db_jcd2 import Stations, Availability, Base

# ✅ Load database credentials from dbinfo.py
USER = db.USER
PASSWORD = db.PASSWORD
PORT = db.PORT
DB = db.DB
URI = db.URI

# ✅ Create connection string
connection_string = f"mysql+pymysql://{USER}:{PASSWORD}@{URI}:{PORT}/{DB}"

# ✅ Create engine and session
engine = create_engine(connection_string, echo=True)
print("🧠 Connected to DB:", engine.url)
Session = sessionmaker(bind=engine)

# ✅ Ensure tables are created (only needed once)
Base.metadata.create_all(engine)


###################### Function to insert station data into the database ######################

def stations_to_db(text_data):
    """ Inserts or updates station metadata into the `stations` table. """
    session = Session()
    try:
        stations = json.loads(text_data)
        station_objects = []
        
        for station in stations:
            station_objects.append(
                Stations(
                    number=station.get('number'),
                    contract_name=station.get('contract_name'),
                    name=station.get('name'),
                    address=station.get('address'),
                    lat=station.get('position', {}).get('lat'),
                    long=station.get('position', {}).get('lng'),
                    banking=bool(station.get('banking')),
                    bonus=bool(station.get('bonus')),
                    bike_stands=station.get('bike_stands')
                )
            )

        session.bulk_save_objects(station_objects)  # ✅ Bulk insert/update
        session.commit()
        print("✅ Station data inserted successfully!")

    except Exception as e:
        session.rollback()
        print("🚨 Error inserting stations:", traceback.format_exc())
    
    finally:
        session.close()

###################### Function to insert availability data ######################

def availability_to_db(text_data):
    """ Inserts or updates real-time bike availability data into the `availability` table. """
    session = Session()
    try:
        stations = json.loads(text_data)

        for station in stations:
            print(f"📌 Debug: Checking station {station.get('number')} at {station.get('last_update')}")

            # ✅ Check if station exists before inserting availability
            station_exists = session.query(Stations).filter_by(number=station.get("number")).first()
            if not station_exists:
                print(f"🚨 Warning: Station {station.get('number')} not found in stations table. Skipping...")
                continue

            availability_entry = Availability(
                station_id=station.get("number"),
                last_update=datetime.utcfromtimestamp(station.get("last_update") / 1000.0),
                available_bikes=station.get("available_bikes"),
                available_bike_stands=station.get("available_bike_stands"),
                status=station.get("status")
            )

            session.merge(availability_entry)  # ✅ Insert or update individually
            print(f"✅ Inserted/Updated: Station {station.get('number')} at {station.get('last_update')}")

        session.commit()
        print("✅ Availability data inserted/updated successfully!")

    except Exception as e:
        session.rollback()
        print("🚨 Error inserting availability:", traceback.format_exc())

    finally:
        session.close()


###################### Fetch Data from JCDecaux API ######################

try:
    # ✅ Fetch data from the JCDecaux API
    response = requests.get(db.STATIONS_URI, params={"apiKey": db.JCKEY, "contract": db.NAME})
    response.raise_for_status()  # Raise error for failed request

    # ✅ Insert station and availability data
    # stations_to_db(response.text)  # Insert station data only once
    availability_to_db(response.text)  # Update availability continuously
    
except Exception as e:
    print("🚨 Error:", traceback.format_exc())