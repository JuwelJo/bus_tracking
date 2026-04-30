from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@router.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = STATIC_DIR / "dashboard.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_alias():
    return dashboard()
