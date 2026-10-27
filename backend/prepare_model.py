"""Prepare a real-data model; print precise training readiness diagnostics."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.clean_data import clean_csv
from ml.train_model import train, prepare_data

RAW = ROOT / "data/raw/kolkata_traffic_weather.csv"
CLEAN = ROOT / "data/processed/kolkata_traffic_weather_clean.csv"
MODEL = ROOT / "ml/artifacts/congestion_model.joblib"


def main():
    if MODEL.exists():
        print("MODEL READY: existing model artifact:", MODEL, flush=True)
        return True
    if not RAW.exists():
        print("MODEL NOT READY: historical CSV missing:", RAW, flush=True)
        return False
    try:
        cleaned = clean_csv(RAW, CLEAN)
        paired = prepare_data(CLEAN)
        print(f"MODEL DATA: {len(cleaned)} clean observations; {len(paired)} valid 15-minute pairs; "
              f"{paired['timestamp_utc'].nunique()} paired timestamps; "
              f"classes={paired['target'].value_counts().to_dict()}", flush=True)
        train(CLEAN, MODEL)
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"MODEL NOT READY: {type(exc).__name__}: {exc}", flush=True)
        print("Continue collecting real 5-minute observations; redeploy to retry training.", flush=True)
        return False
    print("MODEL READY: trained artifact:", MODEL, flush=True)
    return True


if __name__ == "__main__":
    main()
