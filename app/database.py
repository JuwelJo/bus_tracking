from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+mysqlconnector://root:9yjojruvuCOC@localhost:3306/bus_tracking"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ✅ THIS IS WHAT YOU WERE MISSING
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()