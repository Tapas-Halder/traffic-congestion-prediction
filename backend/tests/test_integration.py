"""Offline contract tests; no TomTom/OpenWeather credentials required."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.services.features import build_prediction_features
from traffic_core import classify_traffic, parse_current, parse_prediction, load_history

payload = {
    "collected_at": "2026-10-11T04:30:00+00:00",
    "location": {"latitude": 22.56, "longitude": 88.35},
    "traffic": {"flowSegmentData": {"currentSpeed": 20, "freeFlowSpeed": 40, "confidence": 0.95}},
    "weather": {"main": {"temp": 30, "humidity": 75}, "rain": {"1h": 0}, "wind": {"speed": 2}},
}
features = build_prediction_features(payload)
assert features["hour"] == 10  # 04:30 UTC -> 10:00 IST
assert features["speed_ratio"] == 0.5
assert classify_traffic(20, 40) == "Heavy"
assert parse_current(payload)["traffic"]["current_speed"] == 20
assert parse_prediction({"prediction": "Heavy", "confidence": 0.8})["prediction"] == "Heavy"

try:
    build_prediction_features({**payload, "traffic": {"flowSegmentData": {"freeFlowSpeed": 40}}})
except ValueError:
    pass
else:
    raise AssertionError("Missing speed should be rejected")

client = TestClient(app)
assert client.get("/health").status_code == 200
with patch("app.main.collect_current_data", return_value=payload), patch(
    "app.main.predict", return_value={"prediction": "Heavy", "confidence": 0.8}
):
    current = client.get("/api/v1/data/current", params={"latitude": 22.56, "longitude": 88.35})
    assert current.status_code == 200
    assert parse_current(current.json())["has_any_field"]
    predicted = client.post("/api/v1/predict", json={"latitude": 22.56, "longitude": 88.35})
    assert predicted.status_code == 200
    assert predicted.json()["prediction"] == "Heavy"

csv_path = ROOT / "data/raw/kolkata_traffic_weather.csv"
if csv_path.exists():
    history = load_history(str(csv_path), "Esplanade")
    assert history["message"] is None or "not yet available" in history["message"]
print("PASS: offline API, ML feature, frontend parser and CSV contracts")
