from flask import Blueprint, jsonify, render_template, request
from . import db, cache  # ✅ relative import from within the package
from .models import Availability, Station, WeatherCurrent, WeatherHourly


main = Blueprint('main', __name__)

@main.route('/')
def landing():
    return render_template('index.html')


@main.route('/map')
def map():
    return render_template('map.html')

@main.route('/explore')
def explore():
    return render_template('explore.html')

@main.route("/available", methods=["GET"])
@cache.cached(timeout=300)
def get_all_stations():
    subquery = (
        db.session.query(
            Availability.station_id,
            func.max(Availability.last_update).label("latest_update")
        )
        .group_by(Availability.station_id)
        .subquery()
    )

    latest_stations = (
        db.session.query(
            Station.number,
            Station.contract_name,
            Station.name,
            Station.address,
            Station.lat,
            Station.long,
            Station.banking,
            Station.bonus,
            Station.bike_stands,
            Availability.available_bike_stands,
            Availability.available_bikes,
            Availability.last_update,
            Availability.status
        )
        .join(subquery, subquery.c.station_id == Station.number)
        .join(
            Availability,
            and_(
                Availability.station_id == subquery.c.station_id,
                Availability.last_update == subquery.c.latest_update
            )
        )
        .all()
    )

    station_data_list = [
            {
                "number": station.number,
                "contract_name": station.contract_name,
                "name": station.name,
                "address": station.address,
                "position": {
                    "lat": station.lat,
                    "lng": station.long,
                },
                "banking": bool(station.banking),
                "bonus": bool(station.bonus),
                "bike_stands": station.bike_stands,
                "available_bike_stands": station.available_bike_stands,
                "available_bikes": station.available_bikes,
                "last_update": int(station.last_update.timestamp() * 1000) if station.last_update else None,
                "status": station.status
            }
            for station in latest_stations
        ]

    return jsonify(station_data_list)

@main.route("/station-history/<int:station_id>", methods=["GET"])
def get_station_history(station_id):
    records = (
        db.session.query(Availability)
        .filter_by(station_id=station_id)
        .order_by(Availability.last_update.desc())
        .limit(24)
        .all()
    )

    if not records:
        return jsonify({"error": f"No availability history for station {station_id}"}), 404

    return jsonify([
        {
            "timestamp": record.last_update.strftime("%Y-%m-%d %H:%M:%S"),
            "available_bikes": record.available_bikes,
            "available_bike_stands": record.available_bike_stands
        }
        for record in records
    ])

@main.route("/station-history-all", methods=["GET"])
@cache.cached(timeout=3600)  # Cache for 1 hour
def get_all_station_history():
    """Returns hourly aggregated data for the past 3 days for all stations"""
    # Get data from past 3 days (to ensure we have good coverage)
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    
    # Get all stations
    stations = db.session.query(Station.number).all()
    result = {}
    
    for station_id, in stations:
        # Get all records for this station in the past 3 days
        records = (
            db.session.query(Availability)
            .filter(Availability.station_id == station_id)
            .filter(Availability.last_update >= three_days_ago)
            .order_by(Availability.last_update.asc())
            .all()
        )
        
        # Group by hour (0-23)
        hourly_data = {}
        for record in records:
            hour = record.last_update.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    "bikes_available": record.available_bikes,
                    "stands_available": record.available_bike_stands,
                    "count": 1,
                    "timestamp": record.last_update.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                # Average the values if we have multiple records for this hour
                hourly_data[hour]["bikes_available"] = (
                    hourly_data[hour]["bikes_available"] * hourly_data[hour]["count"] + record.available_bikes
                ) / (hourly_data[hour]["count"] + 1)
                
                hourly_data[hour]["stands_available"] = (
                    hourly_data[hour]["stands_available"] * hourly_data[hour]["count"] + record.available_bike_stands
                ) / (hourly_data[hour]["count"] + 1)
                
                hourly_data[hour]["count"] += 1
        
        # Format the data and store by hour
        formatted_data = {}
        for hour, data in hourly_data.items():
            formatted_data[str(hour)] = {
                "bikes_available": round(data["bikes_available"]),
                "stands_available": round(data["stands_available"])
            }
        
        if formatted_data:
            result[str(station_id)] = formatted_data
    
    return jsonify(result)


@main.route("/weather", methods=["GET"])
@cache.cached(timeout=300)
def get_latest_weather():
    latest_weather = (
        db.session.query(WeatherCurrent)
        .order_by(WeatherCurrent.recorded_at.desc())
        .first()
    )

    if not latest_weather:
        return jsonify({"error": "No weather data available"}), 404

    data = {
        "temperature": round(latest_weather.temp, 1),
        "condition": latest_weather.weather_description.title()
    }

    return jsonify(data)

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "bike_availability_model.pkl")
model = joblib.load(MODEL_PATH)

@main.route("/predict-24h", methods=["GET"])
@cache.cached(timeout=3600)
def predict_24h_all_stations():
    now = datetime.utcnow()
    forecast_rows = (
        db.session.query(WeatherHourly)
        .filter(WeatherHourly.dt >= now)
        .filter(WeatherHourly.dt <= now + timedelta(hours=24))
        .order_by(WeatherHourly.dt.asc())
        .all()
    )

    if not forecast_rows:
        return jsonify({"error": "No forecast data available"}), 400

    df_weather = pd.DataFrame([{
        "forecast_time": row.dt,
        "hour": row.dt.hour,
        "dayofweek": row.dt.weekday(),
        "temp": row.temp,
        "humidity": row.humidity,
        "pressure": row.pressure,
        "wind_speed": row.wind_speed
    } for row in forecast_rows])

    station_ids = [s[0] for s in db.session.query(Station.number).all()]

    records = []
    for station_id in station_ids:
        for _, row in df_weather.iterrows():
            records.append({
                "station_id": station_id,
                "hour": row["hour"],
                "dayofweek": row["dayofweek"],
                "temp": row["temp"],
                "humidity": row["humidity"],
                "wind_speed": row["wind_speed"],
                "pressure": row["pressure"],
                "forecast_time": row["forecast_time"]
            })

    df_input = pd.DataFrame(records)

    df_input["predicted_bikes"] = model.predict(df_input[[
        "station_id", "hour", "dayofweek", "temp", "humidity", "wind_speed", "pressure"
    ]]).round().astype(int)

    output = {}
    for row in df_input.itertuples():
        station_id = int(row.station_id)
        predicted = int(row.predicted_bikes)
        time_str = pd.Timestamp(row.forecast_time).strftime("%Y-%m-%d %H:%M:%S")

        station_data = output.setdefault(station_id, [])
        station_data.append({
            "forecast_time": time_str,
            "predicted_bikes": predicted
        })
        
    return jsonify(output)

