from JCDAPI import dbinfo as db
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, Boolean, PrimaryKeyConstraint, inspect
from sqlalchemy.orm import sessionmaker, relationship, declarative_base


# ✅ Load credentials
USER = db.USER
PASSWORD = db.PASSWORD
PORT = db.PORT
DB = db.DB
URI = db.URI

# ✅ Safe connection string
connection_string = f"mysql+pymysql://{USER}:{PASSWORD}@{URI}:{PORT}/{DB}"
engine = create_engine(connection_string, echo=True)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# ✅ Define tables
class Stations(Base):
    __tablename__ = "stations"
    number = Column(Integer, primary_key=True, nullable=False)
    contract_name = Column(String(255))
    name = Column(String(255))
    address = Column(String(255))
    lat = Column(Float)
    long = Column(Float)
    banking = Column(Boolean)
    bonus = Column(Boolean)
    bike_stands = Column(Integer)

    availability = relationship("Availability", back_populates="station")


class Availability(Base):
    __tablename__ = "availability"
    station_id = Column(Integer, ForeignKey("stations.number", ondelete="CASCADE"), nullable=False)
    last_update = Column(DateTime, nullable=False)
    available_bikes = Column(Integer, nullable=False)
    available_bike_stands = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)

    station = relationship("Stations", back_populates="availability")
    __table_args__ = (PrimaryKeyConstraint("station_id", "last_update"),)

