import importlib
import sys
from pathlib import Path

# Backend is commonly launched from backend/, so make the repository-root ml package importable.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from typing import Any

MODEL_MODULE = "ml.random_forest_model"


def predict(features: dict[str, float]) -> dict[str, Any]:
    """Call the ML team's Python-only Random Forest model.

    The ML team must create ml/random_forest_model.py with:
        def predict_congestion(features: dict[str, float]) -> tuple[str, float | None]:
            ...
    """
    try:
        model_module = importlib.import_module(MODEL_MODULE)
        predict_congestion = getattr(model_module, "predict_congestion")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            "ML model is not available. Add ml/random_forest_model.py "
            "with predict_congestion(features)."
        ) from exc

    result = predict_congestion(features)

    if isinstance(result, tuple):
        prediction, confidence = result
    else:
        prediction, confidence = result, None

    return {
        "prediction": str(prediction),
        "confidence": float(confidence) if confidence is not None else None,
    }
