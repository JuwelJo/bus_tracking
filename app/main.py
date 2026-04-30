from app.routes.admin import router as admin_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.location import router as location_router
from app.database import init_db

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location_router, prefix="")
app.include_router(admin_router)   # ✅ ADD THIS

@app.get("/")
def home():
    return {"message": "Server running 🚍"}