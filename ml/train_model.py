"""Train a Random Forest on cleaned Kolkata traffic/weather history.

Run: python ml/clean_data.py && python ml/train_model.py
Target is the next available observation for the same road, not necessarily +15 minutes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline

FEATURES = ["current_speed", "free_flow_speed", "speed_ratio", "traffic_confidence",
            "temperature", "humidity", "rain_1h", "hour", "day_of_week"]
TARGET = "next_congestion_level"

def build_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{path} missing. Run ml/clean_data.py first.")
    df = pd.read_csv(path)
    required = {"timestamp_utc", "location_id", "current_speed_kmph",
                "free_flow_speed_kmph", "confidence", "temperature_c",
                "humidity_pct", "rain_1h_mm"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp_utc", "location_id"]).copy()
    local = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
    df["hour"], df["day_of_week"] = local.dt.hour.astype(float), local.dt.dayofweek.astype(float)
    df["current_speed"] = pd.to_numeric(df["current_speed_kmph"], errors="coerce")
    df["free_flow_speed"] = pd.to_numeric(df["free_flow_speed_kmph"], errors="coerce")
    df["speed_ratio"] = df["current_speed"] / df["free_flow_speed"].where(df["free_flow_speed"] > 0)
    df["traffic_confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    df["temperature"] = pd.to_numeric(df["temperature_c"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity_pct"], errors="coerce")
    df["rain_1h"] = pd.to_numeric(df["rain_1h_mm"], errors="coerce")
    ratio = df["speed_ratio"]
    df["observed_level"] = "Heavy"
    df.loc[ratio >= 0.70, "observed_level"] = "Moderate"
    df.loc[ratio >= 0.90, "observed_level"] = "Low"
    df = df.sort_values(["location_id", "timestamp_utc"])
    df[TARGET] = df.groupby("location_id")["observed_level"].shift(-1)
    df["next_time"] = df.groupby("location_id")["timestamp_utc"].shift(-1)
    df = df.dropna(subset=[TARGET, "next_time"]).copy()
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        med = df[col].median()
        df[col] = df[col].fillna(0.0 if pd.isna(med) else float(med))
    return df.sort_values("timestamp_utc").reset_index(drop=True)

def train(data_path: Path, model_path: Path) -> None:
    df = build_frame(data_path)
    if len(df) < 30:
        raise ValueError(f"Only {len(df)} labelled rows. Collect more data.")
    cutoff = df["timestamp_utc"].quantile(0.80)
    train_df, test_df = df[df.timestamp_utc <= cutoff], df[df.timestamp_utc > cutoff]
    if train_df.empty or test_df.empty or train_df[TARGET].nunique() < 2:
        raise ValueError("Not enough chronological examples/classes.")
    model = Pipeline([("classifier", RandomForestClassifier(
        n_estimators=200, random_state=42, class_weight="balanced"))])
    model.fit(train_df[FEATURES], train_df[TARGET])
    pred = model.predict(test_df[FEATURES])
    print(f"Train rows: {len(train_df)} | Test rows: {len(test_df)}")
    print(f"Chronological accuracy: {accuracy_score(test_df[TARGET], pred):.3f}")
    print(classification_report(test_df[TARGET], pred, zero_division=0))
    print("Labels are proxy labels derived from next-observation speed ratio.")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "features": FEATURES, "target": TARGET}, model_path)
    print(f"Saved: {model_path}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/processed/kolkata_traffic_weather_clean.csv"))
    parser.add_argument("--model", type=Path, default=Path("ml/artifacts/congestion_model.joblib"))
    args = parser.parse_args()
    train(args.data, args.model)

if __name__ == "__main__":
    main()
