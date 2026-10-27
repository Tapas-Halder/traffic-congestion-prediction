"""Paths and constants for the Kolkata ML pipeline."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ML_DIR = Path(__file__).resolve().parent
RAW_CSV = ROOT / "data/raw/kolkata_traffic_weather.csv"
PROCESSED_CSV = ROOT / "data/processed/kolkata_traffic_weather_clean.csv"
MODEL_PATH = ML_DIR / "artifacts/congestion_model.joblib"
OUTPUT_DIR = ML_DIR / "outputs"
HORIZON_MINUTES = 15
