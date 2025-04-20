from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
cache = Cache()  # ✅ Initialize cache globally

def create_app():
    app = Flask(__name__)

    # ✅ Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://admin:{os.getenv('PASSWORD')}@remotejcddb.cja0m4o064s6.eu-north-1.rds.amazonaws.com:3306/remotejcddb"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CACHE_TYPE"] = "simple"  # ✅ Enable Flask-Caching (in-memory cache)
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # ✅ Cache for 5 minutes

    db.init_app(app)
    cache.init_app(app)  # ✅ Properly register cache with the Flask app

    from .routes import main  # ✅ RELATIVE IMPORT
    app.register_blueprint(main)

    return app
