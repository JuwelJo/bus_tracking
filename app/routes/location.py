from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.database import get_db
from app.models import Location, Stop
from datetime import datetime
import math

router = APIRouter()

# 🔷 REQUEST MODEL
class LocationCreate(BaseModel):
    bus_id: int
    lat: float
    lng: float
    speed: float = Field(0, ge=0)
    gps_time: str | None = None


# 🔷 HAVERSINE
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# 🔷 FIND NEAREST ROUTE POINT
def find_nearest_route_point(bus_lat, bus_lng, db: Session):

    points = db.execute(
        text("SELECT lat, lng FROM route_points ORDER BY sequence_order")
    ).fetchall()

    if not points:
        return None, None

    min_dist = float("inf")
    nearest_index = 0

    for i, p in enumerate(points):   # 🔥 use enumerate
        dist = haversine(bus_lat, bus_lng, p.lat, p.lng)

        if dist < min_dist:
            min_dist = dist
            nearest_index = i        # 🔥 use index (NOT sequence_order)

    return nearest_index, min_dist


# 🔷 CALCULATE DISTANCE ALONG ROUTE (FULL)
def calculate_route_distance(start_index, db: Session):

    points = db.execute(
        text("SELECT * FROM route_points ORDER BY sequence_order")
    ).fetchall()

    total_distance = 0

    for i in range(start_index, len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        total_distance += haversine(p1.lat, p1.lng, p2.lat, p2.lng)

    return total_distance


# 🔷 CALCULATE DISTANCE UNTIL STOP (🔥 IMPORTANT)
def calculate_distance_to_stop(start_index, stop_index, db: Session):

    points = db.execute(
        text("SELECT lat, lng FROM route_points ORDER BY sequence_order")
    ).fetchall()

    if not points:
        return 0

    # convert to list
    coords = [(p.lat, p.lng) for p in points]

    # safety check
    if start_index >= len(coords) or stop_index >= len(coords):
        return 0

    if start_index >= stop_index:
        return 0

    total_distance = 0

    for i in range(start_index, stop_index):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]

        total_distance += haversine(lat1, lon1, lat2, lon2)

    return total_distance


# 🔷 MAP STOPS TO ROUTE
def map_stops_to_route(db: Session):

    stops = db.query(Stop).all()

    route_points = db.execute(
        text("SELECT lat, lng FROM route_points ORDER BY sequence_order")
    ).fetchall()

    stop_mapping = []

    for stop in stops:
        min_dist = float("inf")
        nearest_index = 0

        for i, p in enumerate(route_points):
            dist = haversine(stop.latitude, stop.longitude, p.lat, p.lng)

            if dist < min_dist:
                min_dist = dist
                nearest_index = i

        stop_mapping.append({
            "stop_name": stop.name,
            "index": nearest_index
        })

    return stop_mapping

# 🔷 FIND NEXT STOP
def get_next_stop(bus_index, db: Session):

    stops = map_stops_to_route(db)

    stops = sorted(stops, key=lambda x: x["index"])

    for stop in stops:
        if stop["index"] > bus_index:
            return stop

    return stops[-1] if stops else None


# 🔷 POST LOCATION
@router.post("/location", status_code=201)
def add_location(payload: LocationCreate, db: Session = Depends(get_db)):

    bus = db.execute(
        text("SELECT id FROM buses WHERE id = :id"),
        {"id": payload.bus_id}
    ).fetchone()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    current_time = datetime.utcnow()
    gps_time_obj = None
    if payload.gps_time:
         gps_time_obj = datetime.strptime(payload.gps_time, "%H:%M:%S").time()
    
    loc = Location(
    bus_id=payload.bus_id,
    latitude=payload.lat,
    longitude=payload.lng,
    speed=payload.speed,
    gps_time=gps_time_obj,
    timestamp=current_time
    )

    db.add(loc)
    db.commit()
    db.refresh(loc)

    return {"status": "stored", "id": loc.id}

@router.get("/bus/{bus_id}/location")
def get_location(bus_id: int, db: Session = Depends(get_db)):

    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        raise HTTPException(status_code=404, detail="No location found")

    return {
        "bus_id": loc.bus_id,
        "latitude": float(loc.latitude),
        "longitude": float(loc.longitude),
        "speed": float(loc.speed or 0),
        "timestamp": str(loc.timestamp)
    }

# 🔷 ETA (🔥 FINAL SMART VERSION)
import requests
import os

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

def get_mapbox_route(lat1, lon1, lat2, lon2):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{lon1},{lat1};{lon2},{lat2}?geometries=geojson&access_token={MAPBOX_TOKEN}"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        if "routes" not in data or not data["routes"]:
            return None, None

        route = data["routes"][0]

        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        return distance_km, duration_min

    except Exception as e:
        print("Mapbox error:", e)
        return None, None


@router.get("/bus/{bus_id}/eta")
def get_eta(bus_id: int, db: Session = Depends(get_db)):

    from app.models import Route, RouteStop, Stop
    import math

    # 🔹 helper distance (for nearest stop only)
    def simple_distance(lat1, lon1, lat2, lon2):
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111

    # 🔹 get latest location
    loc = db.query(Location)\
        .filter(Location.bus_id == bus_id)\
        .order_by(Location.timestamp.desc())\
        .first()

    if not loc:
        raise HTTPException(status_code=404, detail="No location found")

    # 🔹 get route
    route = db.query(Route).filter(Route.bus_id == bus_id).first()
    if not route:
        return {"error": "No route found"}

    # 🔹 get ordered stops
    route_stops = db.query(RouteStop)\
        .filter(RouteStop.route_id == route.id)\
        .order_by(RouteStop.stop_order)\
        .all()

    if not route_stops:
        return {"error": "No stops in route"}

    # 🔹 find nearest stop index
    min_dist = float("inf")
    nearest_index = 0

    for i, rs in enumerate(route_stops):
        stop = db.query(Stop).filter(Stop.id == rs.stop_id).first()

        d = simple_distance(
            loc.latitude,
            loc.longitude,
            stop.latitude,
            stop.longitude
        )

        if d < min_dist:
            min_dist = d
            nearest_index = i

    # 🔹 next stop = next in route
    next_index = min(nearest_index + 1, len(route_stops) - 1)
    next_rs = route_stops[next_index]
    stop = db.query(Stop).filter(Stop.id == next_rs.stop_id).first()

    if not stop:
        return {"error": "Stop not found"}

    # 🔥 MAPBOX ROUTE (your existing function)
    distance, eta_minutes = get_mapbox_route(
        loc.latitude,
        loc.longitude,
        stop.latitude,
        stop.longitude
    )

    if distance is None:
        return {"error": "Mapbox route failed"}

    return {
        "bus_id": bus_id,
        "latitude": float(loc.latitude),
        "longitude": float(loc.longitude),
        "next_stop": stop.name,
        "distance_km": round(distance, 3),
        "eta_minutes": round(eta_minutes, 2)
    }
