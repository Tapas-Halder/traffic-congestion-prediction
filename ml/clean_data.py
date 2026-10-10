"""Clean the collected Kolkata traffic/weather CSV.

Usage from repository root:
    python ml/clean_data.py --input data/kolkata_traffic_weather.csv

Writes:
    data/processed/kolkata_traffic_weather_clean.csv

This script does not call external APIs and never reads API keys.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp_utc", "city", "location_id", "road_name", "corridor",
    "latitude", "longitude", "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec", "confidence",
    "road_closure", "temperature_c", "feels_like_c", "humidity_pct",
    "pressure_hpa", "wind_speed_mps", "rain_1h_mm", "weather_main",
    "weather_description",
]
NUMERIC_COLUMNS = [
    "latitude", "longitude", "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec", "confidence",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm",
]
TEXT_COLUMNS = [
    "city", "location_id", "road_name", "corridor", "weather_main",
    "weather_description",
]


def clean_csv(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Validate columns, normalize types, remove duplicates, and save clean CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    df = pd.read_csv(input_path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    # Keep the expected schema and order; do not silently invent observations.
    df = df[REQUIRED_COLUMNS].copy()
    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], errors="coerce", utc=True
    )
    df = df.dropna(subset=["timestamp_utc", "location_id", "road_name"])

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in TEXT_COLUMNS:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace("", pd.NA)

    df["road_closure"] = (
        df["road_closure"].astype("string").str.strip().str.lower()
        .map({"true": True, "1": True, "yes": True,
              "false": False, "0": False, "no": False})
    )

    # Remove impossible readings rather than replacing them with made-up values.
    df.loc[df["current_speed_kmph"] < 0, "current_speed_kmph"] = pd.NA
    df.loc[df["free_flow_speed_kmph"] <= 0, "free_flow_speed_kmph"] = pd.NA
    df.loc[df["current_travel_time_sec"] < 0, "current_travel_time_sec"] = pd.NA
    df.loc[df["free_flow_travel_time_sec"] < 0, "free_flow_travel_time_sec"] = pd.NA
    df.loc[~df["confidence"].between(0, 1), "confidence"] = pd.NA
    df.loc[~df["humidity_pct"].between(0, 100), "humidity_pct"] = pd.NA
    df.loc[df["rain_1h_mm"] < 0, "rain_1h_mm"] = pd.NA
    df.loc[df["wind_speed_mps"] < 0, "wind_speed_mps"] = pd.NA

    # Exact duplicate API snapshots are removed; keep the newest copy.
    df = df.drop_duplicates(
        subset=["timestamp_utc", "location_id"], keep="last"
    )
    df = df.sort_values(["timestamp_utc", "location_id"]).reset_index(drop=True)

    # Store timestamps consistently in ISO-8601 UTC format.
    df["timestamp_utc"] = df["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Input rows: {len(pd.read_csv(input_path))}")
    print(f"Clean rows: {len(df)}")
    print(f"Removed rows: {len(pd.read_csv(input_path)) - len(df)}")
    print(f"Output: {output_path}")
    print("Note: missing measurements remain blank; no fabricated values were added.")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/kolkata_traffic_weather.csv"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/kolkata_traffic_weather_clean.csv"),
    )
    args = parser.parse_args()
    clean_csv(args.input, args.output)


if __name__ == "__main__":
    main()
