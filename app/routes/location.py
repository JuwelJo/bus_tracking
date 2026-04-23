from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Location, Stop
from app.ml.model import predict_eta
import math

router = APIRouter()

# 🔷 Distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lat2 - lat1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# 🔷 POST location (🔥 FIXED)
@router.post("/location")
def add_location(data: dict, db: Session = Depends(get_db)):
    try:
        print("📥 DATA RECEIVED:", data)

        # 🔥 VALIDATION
        if "bus_id" not in data or "lat" not in data or "lng" not in data:
            return {"error": "Missing required fields"}

        bus_id = int(data["bus_id"])
        lat = float(data["lat"])
        lng = float(data["lng"])
        speed = float(data.get("speed", 0))

        # 🔥 CHECK BUS EXISTS (CRITICAL FIX)
        bus = db.execute(
            text("SELECT id FROM buses WHERE id = :id"),
            {"id": bus_id}
        ).fetchone()

        if not bus:
            return {"error": f"Bus ID {bus_id} not found in buses table"}

        # 🔥 INSERT LOCATION
        loc = Location(
            bus_id=bus_id,
            latitude=lat,
            longitude=lng,
            speed=speed
        )

        db.add(loc)
        db.commit()
        db.refresh(loc)

        print("✅ SAVED TO DB")

        return {
            "status": "stored",
            "id": loc.id
        }

    except Exception as e:
        db.rollback()  # 🔥 IMPORTANT
        print("❌ DB ERROR:", e)
        return {"error": str(e)}


# 🔷 GET latest location
@router.get("/bus/{bus_id}/location")
def get_location(bus_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        return {"error": "No location found"}

    return loc


# 🔷 GET ETA
@router.get("/bus/{bus_id}/eta")
def get_eta(bus_id: int, db: Session = Depends(get_db)):

    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        return {"error": "No location found"}

    speed = loc.speed if loc.speed > 0 else 20

    stops = db.query(Stop).all()

    nearest = None
    min_dist = float("inf")

    for stop in stops:
        dist = haversine(loc.latitude, loc.longitude, stop.latitude, stop.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest = stop

    if not nearest:
        return {"error": "No nearest stop found"}

    route = db.execute(
        text("SELECT stop_id, stop_order FROM route_stops")
    ).fetchall()

    current_order = None
    for r in route:
        if r[0] == nearest.id:
            current_order = r[1]
            break

    if current_order is None:
        return {"error": "Stop not in route"}

    next_stop_obj = None
    for r in route:
        if r[1] == current_order + 1:
            next_stop_obj = db.query(Stop).filter(Stop.id == r[0]).first()
            break

    if not next_stop_obj:
        return {"message": "Last stop reached"}

    distance = haversine(
        loc.latitude, loc.longitude,
        next_stop_obj.latitude, next_stop_obj.longitude
    )

    locations = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .limit(10)\
        .all()

    locations = locations[::-1]

    if len(locations) < 4:
        return {
            "bus_id": bus_id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "eta_minutes": 0,
            "next_stop": next_stop_obj.name,
            "distance_km": distance,
            "message": "Collecting data..."
        }

    sequence = []

    for l in locations[-4:]:
        sequence.append([
            l.latitude,
            l.longitude,
            l.speed if l.speed > 0 else 20,
            next_stop_obj.id,
            distance
        ])

    print("📊 FINAL SEQUENCE:", sequence)

    try:
        eta_minutes = predict_eta(sequence)
    except Exception as e:
        print("❌ MODEL ERROR:", e)
        eta_minutes = 0

    return {
        "bus_id": bus_id,
        "next_stop": next_stop_obj.name,
        "distance_km": distance,
        "eta_minutes": eta_minutes,
        "latitude": loc.latitude,
        "longitude": loc.longitude
    }


# 🔷 NEAREST STOP
@router.get("/bus/{bus_id}/nearest-stop")
def nearest_stop(bus_id: int, db: Session = Depends(get_db)):

    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        return {"error": "No location"}

    stops = db.query(Stop).all()

    nearest = None
    min_dist = float("inf")

    for stop in stops:
        dist = haversine(loc.latitude, loc.longitude, stop.latitude, stop.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest = stop

    return {
        "nearest_stop": nearest.name,
        "distance_km": min_dist
    }


# 🔷 NEXT STOP
@router.get("/bus/{bus_id}/next-stop")
def next_stop(bus_id: int, db: Session = Depends(get_db)):

    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        return {"error": "No location"}

    stops = db.query(Stop).all()

    nearest = None
    min_dist = float("inf")

    for stop in stops:
        dist = haversine(loc.latitude, loc.longitude, stop.latitude, stop.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest = stop

    route = db.execute(text("SELECT stop_id, stop_order FROM route_stops")).fetchall()

    current_order = None
    for r in route:
        if r[0] == nearest.id:
            current_order = r[1]
            break

    next_stop_obj = None
    for r in route:
        if r[1] == current_order + 1:
            next_stop_obj = db.query(Stop).filter(Stop.id == r[0]).first()
            break

    return {
        "current_stop": nearest.name,
        "next_stop": next_stop_obj.name if next_stop_obj else "Last stop"
    }