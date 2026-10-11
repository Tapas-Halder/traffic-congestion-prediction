"""Executable smoke and validation tests: python ml/test_model.py."""
import math
from pathlib import Path
import tempfile

import joblib
import pandas as pd

try:
    from ml.clean_data import clean_csv
    from ml.train_model import FEATURES, prepare_data, train
    from ml.random_forest_model import load_model, predict_congestion
except ModuleNotFoundError:
    from clean_data import clean_csv
    from train_model import FEATURES, prepare_data, train
    from random_forest_model import load_model, predict_congestion


def expect_value_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


def main():
    raw = Path("data/raw/kolkata_traffic_weather.csv")
    if raw.is_file():
        with tempfile.TemporaryDirectory() as folder:
            cleaned = Path(folder) / "clean.csv"
            clean_csv(raw, cleaned)
            data = pd.read_csv(cleaned)
            assert len(data) > 0
            pairs = prepare_data(cleaned)
            assert (pairs["next_time"] > pairs["timestamp_utc"]).all()
            offsets = (pairs["next_time"] - pairs["timestamp_utc"]).dt.total_seconds() / 60
            assert offsets.between(10, 20).all()
            print("PASS: CSV cleaning and 15-minute target validation")
    else:
        print("SKIP: raw CSV unavailable; cleaning integration test not run")

    expect_value_error(lambda: predict_congestion({}))
    print("PASS: missing feature validation")
    model_file = Path(__file__).resolve().parent / "artifacts" / "congestion_model.joblib"
    if not model_file.exists():
        print("SKIP: trained artifact unavailable; run clean_data.py and train_model.py first")
        return
    bundle = load_model()
    assert bundle["features"] == FEATURES
    assert set(bundle["pipeline"].classes_).issubset({"Low", "Moderate", "Heavy"})
    sample = {
        "current_speed": 20, "free_flow_speed": 40, "speed_ratio": 0.5,
        "traffic_confidence": 0.95, "temperature": 29, "humidity": 70,
        "rain_1h": 0, "hour": 9, "day_of_week": 1,
    }
    label, confidence = predict_congestion(sample)
    assert label in {"Low", "Moderate", "Heavy"}
    assert confidence is None or 0 <= confidence <= 1
    expect_value_error(lambda: predict_congestion({**sample, "free_flow_speed": 0}))
    expect_value_error(lambda: predict_congestion({**sample, "hour": 25}))
    expect_value_error(lambda: predict_congestion({**sample, "speed_ratio": math.inf}))
    expect_value_error(lambda: predict_congestion({**sample, "speed_ratio": 0.9}))
    print("PASS: prediction and invalid input tests")


if __name__ == "__main__":
    main()
