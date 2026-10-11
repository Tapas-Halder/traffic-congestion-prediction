from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import PredictionRequest
from app.services.collector import collect_current_data
from app.services.features import build_prediction_features
from app.services.predictor import predict

app = FastAPI(title="Kolkata Traffic Congestion API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "city": settings.city,
        "tomtom_configured": bool(settings.tomtom_api_key),
        "openweather_configured": bool(settings.openweather_api_key),
    }


@app.get("/api/v1/data/current")
def current_data(
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
) -> dict:
    try:
        return collect_current_data(latitude, longitude)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"External API request failed: {exc}") from exc


@app.post("/api/v1/predict")
def prediction(request: PredictionRequest) -> dict:
    """Collect live inputs, prepare ML features, and run the trained model."""
    try:
        payload = collect_current_data(request.latitude, request.longitude)
        features = build_prediction_features(payload)
        result = predict(features)
        return {
            "city": settings.city,
            "location": payload["location"],
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "source": "TomTom + OpenWeather + ML model",
            "collected_at": payload["collected_at"],
        }
    except (RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Prediction pipeline failed: {exc}") from exc


@app.get("/api/v1/model/status")
def model_status() -> dict:
    """Check model availability without calling paid external APIs."""
    from app.services.predictor import REPO_ROOT
    from ml.random_forest_model import MODEL_PATH, load_model
    if not MODEL_PATH.is_file():
        return {"ready": False, "reason": "Model artifact missing; inspect Render build logs for MODEL NOT READY",
                "model_path": str(MODEL_PATH)}
    try:
        bundle = load_model()
        return {"ready": True, "horizon_minutes": bundle.get("horizon_minutes"),
                "features": bundle.get("features")}
    except (ValueError, FileNotFoundError, KeyError, TypeError) as exc:
        return {"ready": False, "reason": str(exc)}
