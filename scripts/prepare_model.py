"""Prepare a real-data ML artifact during Streamlit deployment."""
from pathlib import Path
import sys

# Direct script execution puts scripts/ on sys.path, not the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.clean_data import clean_csv
from ml.train_model import train

RAW = ROOT / "data/raw/kolkata_traffic_weather.csv"
CLEAN = ROOT / "data/processed/kolkata_traffic_weather_clean.csv"
MODEL = ROOT / "ml/artifacts/congestion_model.joblib"

def main():
    if MODEL.exists():
        print("Existing model artifact found.")
        return
    if not RAW.exists():
        print("No historical CSV yet; live data remains available, ML predictions unavailable.")
        return
    try:
        clean_csv(RAW, CLEAN)
        train(CLEAN, MODEL)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Model preparation skipped: {exc}. Collect more historical data.")
if __name__ == "__main__":
    main()
