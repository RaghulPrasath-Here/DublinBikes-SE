from . import db  # ✅ relative import from the current package  # 

class Station(db.Model):
    __tablename__ = "stations"
    number = db.Column(db.Integer, primary_key=True)  # ✅ Use 'number' instead of 'station_id'
    contract_name = db.Column(db.String(255))
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)  # ✅ Match column name exactly as in MySQL
    banking = db.Column(db.Boolean)
    bonus = db.Column(db.Boolean)
    bike_stands = db.Column(db.Integer)

class Availability(db.Model):
    __tablename__ = "availability"
    station_id = db.Column(db.Integer, db.ForeignKey("stations.number"), primary_key=True)  # ✅ Reference 'number'
    last_update = db.Column(db.DateTime, primary_key=True)
    available_bikes = db.Column(db.Integer)
    available_bike_stands = db.Column(db.Integer)
    status = db.Column(db.String(50))  # ✅ Added 'status' column as per MySQL schema


class WeatherHourly(db.Model):
    __tablename__ = 'hourlyWeather'

    dt = db.Column(db.DateTime, primary_key=True)
    temp = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    pressure = db.Column(db.Integer)
    wind_speed = db.Column(db.Float)
    weather_id = db.Column(db.Integer)
    weather_category = db.Column(db.String(50))
    weather_description = db.Column(db.String(100))
    rain_1h = db.Column(db.Float)
    snow_1h = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime)



class WeatherCurrent(db.Model):
    __tablename__ = 'currentWeather'  # ✅ Corrected table name

    dt = db.Column(db.DateTime, primary_key=True)
    temp = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    pressure = db.Column(db.Integer)
    wind_speed = db.Column(db.Float)
    wind_gust = db.Column(db.Float)
    weather_id = db.Column(db.Integer)
    weather_description = db.Column(db.String(255))  # ✅ Match varchar(255)
    rain_1h = db.Column(db.Float)
    snow_1h = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime)

