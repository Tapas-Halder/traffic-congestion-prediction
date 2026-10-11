"""Validated FastAPI-friendly prediction helper for the saved ML model."""
from functools import lru_cache
from pathlib import Path
import math

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "congestion_model.joblib"
FEATURES = [
    "current_speed", "free_flow_speed", "speed_ratio",
    "traffic_confidence", "temperature", "humidity", "rain_1h",
    "hour", "day_of_week",
]


@lru_cache(maxsize=1)
def load_model():
    """Load only trusted, locally generated model artifacts once per process."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model missing: {MODEL_PATH}. Run training first.")
    bundle = joblib.load(MODEL_PATH)
    if bundle.get("features") != FEATURES or "pipeline" not in bundle:
        raise ValueError("Saved model feature schema does not match prediction code")
    return bundle


def predict_congestion(features: dict):
    """Return (Low/Moderate/Heavy, model_probability); inputs use FEATURES keys."""
    if not isinstance(features, dict):
        raise ValueError("features must be a dictionary")
    missing = [name for name in FEATURES if name not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    values = {}
    for name in FEATURES:
        raw = features[name]
        if raw is None and name in ("temperature", "humidity", "rain_1h",
                                    "traffic_confidence"):
            values[name] = float("nan")
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Invalid numeric feature: {name}") from exc
        if not math.isfinite(value):
            raise ValueError(f"Non-finite feature: {name}")
        values[name] = value
    if values["current_speed"] < 0 or values["free_flow_speed"] <= 0:
        raise ValueError("Speeds must be nonnegative and free_flow_speed positive")
    if values["speed_ratio"] < 0 or not math.isclose(
        values["speed_ratio"],
        values["current_speed"] / values["free_flow_speed"],
        rel_tol=0.02, abs_tol=0.02,
    ):
        raise ValueError("speed_ratio must equal current_speed / free_flow_speed")
    for name, low, high in [("hour", 0, 23), ("day_of_week", 0, 6),
                            ("traffic_confidence", 0, 1), ("humidity", 0, 100)]:
        if not math.isnan(values[name]) and not low <= values[name] <= high:
            raise ValueError(f"{name} must be between {low} and {high}")
    if any(values[name] < 0 for name in ("rain_1h",) if not math.isnan(values[name])):
        raise ValueError("rain_1h cannot be negative")
    if not values["hour"].is_integer() or not values["day_of_week"].is_integer():
        raise ValueError("hour and day_of_week must be integers")
    bundle = load_model()
    model = bundle["pipeline"]
    X = pd.DataFrame([values], columns=FEATURES)
    label = str(model.predict(X)[0])
    if label not in ("Low", "Moderate", "Heavy"):
        raise ValueError(f"Unexpected predicted label: {label}")
    confidence = (float(model.predict_proba(X)[0].max())
                  if hasattr(model, "predict_proba") else None)
    return label, confidence
