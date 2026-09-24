from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import APP_NAME, FRONTEND_URL
from routers.traffic import router

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else [x.strip() for x in FRONTEND_URL.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve the complete HTML/CSS/JS website from the same Render service.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
