import requests
from sqlalchemy import create_engine, text

engine = create_engine("mysql+mysqlconnector://root:9yjojruvuCOC@localhost:3306/bus_tracking")

import os

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

start = "76.950577,8.544067"
end = "76.960000,8.550000"

url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start};{end}?steps=true&geometries=geojson&access_token={MAPBOX_TOKEN}"

response = requests.get(url)
data = response.json()

if "routes" not in data:
    print("ERROR:", data)
    exit()

steps = data["routes"][0]["legs"][0]["steps"]

print("Saving HIGH RESOLUTION route...")

with engine.connect() as conn:

    seq = 0

    for step in steps:
        coords = step["geometry"]["coordinates"]

        for point in coords:
            lng, lat = point

            conn.execute(
                text("""
                    INSERT INTO route_points (route_id, lat, lng, sequence_order)
                    VALUES (:r, :lat, :lng, :seq)
                """),
                {
                    "r": 1,
                    "lat": lat,
                    "lng": lng,
                    "seq": seq
                }
            )

            seq += 1

    conn.commit()

print("✅ HIGH RESOLUTION ROUTE SAVED!")