from flask import Blueprint, jsonify, render_template, request
from . import db, cache  # ✅ relative import from within the package
from .models import Availability, Station, WeatherCurrent, WeatherHourly


main = Blueprint('main', __name__)

@main.route('/')
def landing():
    return render_template('index.html')
