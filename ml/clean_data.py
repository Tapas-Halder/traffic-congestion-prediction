from pathlib import Path
import argparse
import pandas as pd

REQUIRED = [
    "timestamp_utc", "city", "location_id", "road_name", "corridor",
    "latitude", "longitude", "current_speed_kmph",
    "free_flow_speed_kmph", "current_travel_time_sec",
    "free_flow_travel_time_sec", "confidence", "road_closure",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm", "weather_main",
    "weather_description",
]

NUMERIC = [
    "latitude", "longitude", "current_speed_kmph",
    "free_flow_speed_kmph", "current_travel_time_sec",
    "free_flow_travel_time_sec", "confidence", "temperature_c",
    "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm",
]


def clean_csv(source, destination):
    source = Path(source)
    destination = Path(destination)

    df = pd.read_csv(source)
    missing = set(REQUIRED) - set(df.columns)

    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")

    df = df[REQUIRED].copy()
    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], utc=True, errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp_utc", "location_id", "road_name"]
    )

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in [
        "city", "location_id", "road_name", "corridor",
        "weather_main", "weather_description",
    ]:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace("", pd.NA)

    df["road_closure"] = (
        df["road_closure"].astype("string").str.lower().str.strip()
        .map({
            "true": True, "1": True, "yes": True,
            "false": False, "0": False, "no": False,
        })
    )

    # Remove impossible readings; don't invent missing values.
    df.loc[df["current_speed_kmph"] < 0, "current_speed_kmph"] = pd.NA
    df.loc[df["free_flow_speed_kmph"] <= 0, "free_flow_speed_kmph"] = pd.NA
    df.loc[df["current_travel_time_sec"] < 0,
           "current_travel_time_sec"] = pd.NA
    df.loc[df["free_flow_travel_time_sec"] < 0,
           "free_flow_travel_time_sec"] = pd.NA
    df.loc[~df["confidence"].between(0, 1), "confidence"] = pd.NA
    df.loc[~df["humidity_pct"].between(0, 100), "humidity_pct"] = pd.NA
    df.loc[df["rain_1h_mm"] < 0, "rain_1h_mm"] = pd.NA
    df.loc[df["wind_speed_mps"] < 0, "wind_speed_mps"] = pd.NA

    # One record per location and timestamp.
    df = df.drop_duplicates(
        subset=["timestamp_utc", "location_id"], keep="last"
    )

    df = df.sort_values(
        ["timestamp_utc", "location_id"]
    ).reset_index(drop=True)

    destination.parent.mkdir(parents=True, exist_ok=True)
    df["timestamp_utc"] = df["timestamp_utc"].map(
        lambda x: x.isoformat() if pd.notna(x) else ""
    )
    df.to_csv(destination, index=False)

    print("Cleaned rows:", len(df))
    print("Saved to:", destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", default="data/raw/kolkata_traffic_weather.csv"
    )
    parser.add_argument(
        "--output",
        default="data/processed/kolkata_traffic_weather_clean.csv",
    )
    args = parser.parse_args()
    clean_csv(args.input, args.output)