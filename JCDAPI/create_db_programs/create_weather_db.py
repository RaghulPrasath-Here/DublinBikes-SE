# Import necessary libraries
from sqlalchemy import create_engine, text, inspect
from JCDAPI import dbinfo as db  # Adjust if dbinfo is in a different location

# ✅ Load database credentials
USER = db.USER
PASSWORD = db.PASSWORD
PORT = db.PORT
DB = db.DB
URI = db.URI

# ✅ Connect to your real DB
connection_string = f"mysql+pymysql://{USER}:{PASSWORD}@{URI}:{PORT}/{DB}"
engine = create_engine(connection_string, echo=True)

# ✅ Create the weather tables ONLY IF THEY DON’T EXIST
sql_currentWeather = text('''
CREATE TABLE IF NOT EXISTS currentWeather (
    dt DATETIME NOT NULL,
    temp DECIMAL(5,2) NOT NULL,
    feels_like DECIMAL(5,2) NOT NULL,
    humidity INT NOT NULL,
    pressure INT NOT NULL,
    wind_speed DECIMAL(5,2) NOT NULL,
    wind_gust DECIMAL(5,2),
    weather_id INT NOT NULL,
    weather_description VARCHAR(255) NOT NULL,
    rain_1h DECIMAL(5,2),
    snow_1h DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dt)
);
''')

sql_hourlyWeather = text('''
CREATE TABLE IF NOT EXISTS hourlyWeather (
    dt DATETIME NOT NULL,
    temp DECIMAL(5,2) NOT NULL,
    feels_like DECIMAL(5,2) NOT NULL,
    humidity INT NOT NULL,
    pressure INT NOT NULL,
    wind_speed DECIMAL(5,2) NOT NULL,
    weather_id INT NOT NULL,
    weather_category VARCHAR(20) NOT NULL,
    weather_description VARCHAR(255) NOT NULL,
    rain_1h DECIMAL(5,2),
    snow_1h DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dt, recorded_at)
);
''')

# ✅ Execute table creation
with engine.connect() as conn:
    conn.execute(sql_currentWeather)
    conn.execute(sql_hourlyWeather)
    conn.commit()

# 🔍 Optional: show existing tables
inspector = inspect(engine)
print("✅ Weather DB tables found:")
for table in inspector.get_table_names():
    print(f"  - {table}")
