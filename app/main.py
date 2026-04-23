from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ FIRST create app
app = FastAPI()

# ✅ THEN add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 your routes import
from app.routes import location

app.include_router(location.router)