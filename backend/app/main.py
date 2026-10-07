from fastapi import FastAPI, HTTPException, Query
from app.config import settings
from app.services.collector import collect_current_data

app = FastAPI(title="Kolkata Traffic Congestion API", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "city": settings.city}

@app.get("/api/v1/data/current")
def current_data(
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
) -> dict:
    try:
        return collect_current_data(latitude, longitude)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"External API request failed: {exc}") from exc
