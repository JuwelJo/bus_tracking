from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from app.database import Base
from datetime import datetime

# 🔷 BUS TABLE
class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(20))


# 🔷 LOCATION TABLE
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


# 🔷 STOP TABLE
class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)