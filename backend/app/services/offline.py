
"""Offline prediction using real historical Kolkata CSV data."""

from pathlib import Path

import pandas as pd

from app.services.predictor import predict

ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = ROOT / "data" / "raw" / "kolkata_traffic_weather.csv"


def predict_offline(location_id=None):
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Historical CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    required = [
        "timestamp_utc", "location_id",
        "current_speed_kmph", "free_flow_speed_kmph",
        "confidence", "temperature_c",
        "humidity_pct", "rain_1h_mm",
    ]

    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], utc=True, errors="coerce"
    )

    if location_id is not None:
        df = df[
            df["location_id"].astype(str) == str(location_id)
        ].copy()

    df = df.dropna(subset=["timestamp_utc"])
    df = df.sort_values("timestamp_utc", ascending=False)

    for _, row in df.iterrows():
        current = pd.to_numeric(
            row["current_speed_kmph"], errors="coerce"
        )
        free = pd.to_numeric(
            row["free_flow_speed_kmph"], errors="coerce"
        )

        if pd.isna(current) or pd.isna(free):
            continue
        if current < 0 or free <= 0:
            continue

        local_time = row["timestamp_utc"].tz_convert("Asia/Kolkata")

        def optional_number(column):
            value = pd.to_numeric(row[column], errors="coerce")
            return None if pd.isna(value) else float(value)

        features = {
            "current_speed": float(current),
            "free_flow_speed": float(free),
            "speed_ratio": float(current / free),
            "traffic_confidence": optional_number("confidence"),
            "temperature": optional_number("temperature_c"),
            "humidity": optional_number("humidity_pct"),
            "rain_1h": optional_number("rain_1h_mm"),
            "hour": float(local_time.hour),
            "day_of_week": float(local_time.dayofweek),
        }

        result = predict(features)

        return {
            "city": "Kolkata",
            "mode": "historical_offline",
            "location_id": str(row["location_id"]),
            "observed_at": row["timestamp_utc"].isoformat(),
            "prediction_horizon_minutes": 15,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "source": "Historical TomTom + OpenWeather CSV",
            "live_data": False,
        }

    raise ValueError("No valid historical observation found")
