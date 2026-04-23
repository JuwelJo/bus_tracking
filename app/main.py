from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import location  # your existing route

app = FastAPI()

# CORS (important for Flutter later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes
app.include_router(location.router)