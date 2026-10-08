import os
from typing import Any

MODEL_PATH = os.getenv("MODEL_PATH", "../ml/model.joblib")


def predict(features: dict[str, float]) -> dict[str, Any]:
    """Run the trained ML model when it is available.

    The ML team should provide a joblib model whose predict() accepts the feature
    order documented in backend/README.md.
    """
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError("ML model is not available yet. Set MODEL_PATH after the ML team supplies model.joblib")

    try:
        import joblib
    except ImportError as exc:
        raise RuntimeError("joblib is required to load the trained ML model") from exc

    model = joblib.load(MODEL_PATH)
    feature_order = [
        "current_speed", "free_flow_speed", "speed_ratio",
        "traffic_confidence", "temperature", "humidity", "rain_1h",
        "hour", "day_of_week",
    ]
    values = [[features[name] for name in feature_order]]
    prediction = model.predict(values)[0]

    confidence = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(values)[0]
        confidence = float(max(probabilities))

    return {"prediction": str(prediction), "confidence": confidence}
