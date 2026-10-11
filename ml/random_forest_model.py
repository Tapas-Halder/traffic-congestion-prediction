from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = (
    Path(__file__).parent /
    "artifacts" /
    "congestion_model.joblib"
)

FEATURES = [
    "current_speed", "free_flow_speed", "speed_ratio",
    "traffic_confidence", "temperature", "humidity",
    "rain_1h", "hour", "day_of_week",
]


def predict_congestion(features: dict):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model missing. Run python ml/train_model.py first."
        )

    missing = [key for key in FEATURES if key not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    bundle = joblib.load(MODEL_PATH)
    X = pd.DataFrame([
        {key: float(features[key]) for key in FEATURES}
    ])

    model = bundle["pipeline"]
    label = str(model.predict(X)[0])

    confidence = None
    if hasattr(model, "predict_proba"):
        confidence = float(max(model.predict_proba(X)[0]))

    return label, confidence