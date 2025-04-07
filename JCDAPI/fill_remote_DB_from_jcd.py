from JCDAPI import dbinfo as db
import traceback
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