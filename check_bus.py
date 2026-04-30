from app.database import SessionLocal

db = SessionLocal()
try:
    result = db.execute("SELECT * FROM buses WHERE id = 6097").fetchone()
    print("Bus exists:", result is not None)
    if result:
        print("Bus data:", result)
    else:
        print("Bus 6097 not found. Creating it...")
        db.execute("INSERT INTO buses (id, bus_number) VALUES (6097, 'Bus 6097')")
        db.commit()
        print("Bus created successfully")
except Exception as e:
    print("Error:", e)
finally:
    db.close()