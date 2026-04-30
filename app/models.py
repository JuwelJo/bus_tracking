from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Time
from app.database import Base
from datetime import datetime

# 🔷 BUS TABLE
class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(20))
    seating_capacity = Column(Integer)

    # ✅ ADD THESE
    title = Column(String(100))
    driver_name = Column(String(100))
    vehicle_number = Column(String(50))
    active = Column(Integer, default=1)


# 🔷 LOCATION TABLE
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    gps_time = Column(Time)


# 🔷 STOP TABLE
class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)


# 🔷 ROUTE TABLE
class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))


# 🔷 ROUTE_STOPS TABLE
class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    stop_id = Column(Integer, ForeignKey("stops.id"))
    stop_order = Column(Integer)
    morning_time = Column(Time)
    evening_time = Column(Time)