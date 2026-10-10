"""FastAPI-compatible entry point for the trained Random Forest model."""
from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).parent / "artifacts" / "congestion_model.joblib"
FEATURES = ["current_speed", "free_flow_speed", "speed_ratio", "traffic_confidence",
            "temperature", "humidity", "rain_1h", "hour", "day_of_week"]

def predict_congestion(features: dict[str, float]) -> tuple[str, float | None]:
    """Return (congestion label, maximum class probability)."""
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found at {MODEL_PATH}; run python ml/train_model.py.")
    missing = [name for name in FEATURES if name not in features]
    if missing:
        raise ValueError(f"Missing model features: {missing}")
    bundle = joblib.load(MODEL_PATH)
    X = pd.DataFrame([{name: float(features[name]) for name in FEATURES}])
    pipeline = bundle["pipeline"]
    label = str(pipeline.predict(X)[0])
    confidence = float(max(pipeline.predict_proba(X)[0])) if hasattr(pipeline, "predict_proba") else None
    return label, confidence
