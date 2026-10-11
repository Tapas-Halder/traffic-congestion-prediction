"""In-process API adapter for Streamlit Community Cloud (no separate server)."""
import sys
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))
from app.services.collector import collect_current_data
from app.services.features import build_prediction_features
from app.services.predictor import predict

def local_call(method, path, params=None, json_body=None):
    data = json_body or params or {}
    lat, lon = data.get("latitude"), data.get("longitude")
    if path == "/health":
        return {"status": "ok", "mode": "in-process"}
    if path == "/api/v1/data/current" and method == "GET":
        return collect_current_data(lat, lon)
    if path == "/api/v1/predict" and method == "POST":
        observation = collect_current_data(lat, lon)
        outcome = predict(build_prediction_features(observation))
        return {"prediction": outcome["prediction"], "confidence": outcome["confidence"],
                "location": observation["location"], "collected_at": observation["collected_at"],
                "source": "TomTom + OpenWeather + ML model"}
    raise ValueError("Unknown local endpoint: " + path)
