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

