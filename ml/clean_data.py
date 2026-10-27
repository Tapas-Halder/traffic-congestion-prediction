"""Validate and clean TomTom/OpenWeather CSV observations."""
import argparse
from pathlib import Path

import pandas as pd

REQUIRED = [
    "timestamp_utc", "city", "location_id", "road_name", "corridor",
    "latitude", "longitude", "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec", "confidence",
    "road_closure", "temperature_c", "feels_like_c", "humidity_pct",
    "pressure_hpa", "wind_speed_mps", "rain_1h_mm", "weather_main",
    "weather_description",
]
NUMERIC = [
    "latitude", "longitude", "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec", "confidence",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm",
]


def clean_csv(source, destination):
    """Keep valid location/time records; never fabricate traffic measurements."""
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {source}")
    try:
        df = pd.read_csv(source)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("Input CSV is empty") from exc
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")
    if df.empty:
        raise ValueError("Input CSV has no observations")

    original = len(df)
    df = df[REQUIRED].copy()
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    for column in ["city", "location_id", "road_name", "corridor",
                   "weather_main", "weather_description"]:
        df[column] = df[column].astype("string").str.strip().replace("", pd.NA)
    df = df.dropna(subset=["timestamp_utc", "location_id", "road_name"]).copy()

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    limits = {
        "latitude": (-90, 90), "longitude": (-180, 180),
        "confidence": (0, 1), "humidity_pct": (0, 100),
    }
    for column, (low, high) in limits.items():
        df.loc[~df[column].between(low, high), column] = float("nan")
    for column in ["current_speed_kmph", "current_travel_time_sec",
                   "free_flow_travel_time_sec", "wind_speed_mps", "rain_1h_mm"]:
        df.loc[df[column] < 0, column] = float("nan")
    df.loc[df["free_flow_speed_kmph"] <= 0, "free_flow_speed_kmph"] = float("nan")

    closure = df["road_closure"].astype("string").str.strip().str.lower()
    df["road_closure"] = closure.map({
        "true": True, "1": True, "yes": True,
        "false": False, "0": False, "no": False,
    }).astype("boolean")
    df = (df.drop_duplicates(subset=["timestamp_utc", "location_id"], keep="last")
            .sort_values(["timestamp_utc", "location_id"]).reset_index(drop=True))
    if df.empty:
        raise ValueError("No valid observations after cleaning")

    destination.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False)
    print(f"Rows: {original} input, {len(df)} cleaned, {original - len(df)} removed")
    print("Missing traffic speeds:", int(df["current_speed_kmph"].isna().sum()))
    print("Unknown road closures:", int(df["road_closure"].isna().sum()))
    print("Saved to:", destination)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/kolkata_traffic_weather.csv")
    parser.add_argument("--output", default="data/processed/kolkata_traffic_weather_clean.csv")
    args = parser.parse_args()
    clean_csv(args.input, args.output)
