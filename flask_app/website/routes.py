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

