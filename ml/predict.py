"""Prediction helper for the FastAPI backend."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

DEFAULT_MODEL_PATH = Path(__file__).parent / "artifacts" / "congestion_model.joblib"


def load_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Load the saved training bundle."""
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {model_path}. Run ml/train_model.py first."
        )
    return joblib.load(model_path)


def predict_congestion(
    observation: dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """Predict congestion at the next available observation for a road.

    Required keys: timestamp_utc and all training feature columns. This predicts a
    class, not travel time; the target horizon depends on the collection interval.
    """
    bundle = load_model(model_path)
    timestamp = pd.to_datetime(observation.get("timestamp_utc"), utc=True, errors="coerce")
    if pd.isna(timestamp):
        raise ValueError("A valid timestamp_utc is required.")

    row = dict(observation)
    local_time = timestamp.tz_convert("Asia/Kolkata")
    row["hour"] = int(local_time.hour)
    row["day_of_week"] = int(local_time.dayofweek)

    features = bundle["features"]
    missing = [name for name in features if name not in row]
    if missing:
        raise ValueError(f"Missing prediction fields: {missing}")

    X = pd.DataFrame([{name: row[name] for name in features}])
    prediction = str(bundle["pipeline"].predict(X)[0])
    result: dict[str, Any] = {
        "predicted_congestion_level": prediction,
        "prediction_horizon": "next available observation (collection interval dependent)",
    }
    if hasattr(bundle["pipeline"], "predict_proba"):
        probabilities = bundle["pipeline"].predict_proba(X)[0]
        result["probabilities"] = {
            str(label): round(float(prob), 4)
            for label, prob in zip(bundle["pipeline"].classes_, probabilities)
        }
    return result
