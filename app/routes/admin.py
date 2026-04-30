from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bus

router = APIRouter(prefix="/admin")

# 🔷 GET all buses
@router.get("/buses")
def get_buses(db: Session = Depends(get_db)):
    buses = db.query(Bus).all()
    return {
        "success": True,
        "data": buses
    }

# 🔷 CREATE bus
@router.post("/buses")
def create_bus(payload: dict, db: Session = Depends(get_db)):

    # check duplicate
    exists = db.query(Bus).filter(Bus.id == payload["busId"]).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bus already exists")

    bus = Bus(
        id=payload["busId"],
        bus_number=payload.get("busNumber"),
        seating_capacity=payload.get("capacity"),
        title=payload.get("title"),
        driver_name=payload.get("driverName"),
        vehicle_number=payload.get("vehicleNumber"),
        active=1
    )

    db.add(bus)
    db.commit()

    return {
        "success": True,
        "data": payload
    }

from app.models import Stop, Route, RouteStop

# 🔷 ADD STOP TO ROUTE
@router.post("/routes/{bus_id}/stops")
def add_stop(bus_id: int, payload: dict, db: Session = Depends(get_db)):

    # create stop
    stop = Stop(
        name=payload["name"],
        latitude=payload["latitude"],
        longitude=payload["longitude"]
    )
    db.add(stop)
    db.commit()
    db.refresh(stop)

    # get or create route
    route = db.query(Route).filter(Route.bus_id == bus_id).first()
    if not route:
        route = Route(bus_id=bus_id)
        db.add(route)
        db.commit()
        db.refresh(route)

    # find next order
    last = db.query(RouteStop)\
        .filter(RouteStop.route_id == route.id)\
        .order_by(RouteStop.stop_order.desc())\
        .first()

    next_order = last.stop_order + 1 if last else 0

    # add route stop
    rs = RouteStop(
        route_id=route.id,
        stop_id=stop.id,
        stop_order=next_order
    )

    db.add(rs)
    db.commit()

    return {
        "success": True,
        "message": "Stop added"
    }

# 🔷 GET ROUTE WITH STOPS
@router.get("/routes/{bus_id}")
def get_route(bus_id: int, db: Session = Depends(get_db)):

    route = db.query(Route).filter(Route.bus_id == bus_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stops = db.query(RouteStop)\
        .filter(RouteStop.route_id == route.id)\
        .order_by(RouteStop.stop_order)\
        .all()

    result = []

    for rs in stops:
        stop = db.query(Stop).filter(Stop.id == rs.stop_id).first()

        result.append({
            "name": stop.name,
            "latitude": stop.latitude,
            "longitude": stop.longitude,
            "order": rs.stop_order
        })

    return {
        "success": True,
        "data": result
    }