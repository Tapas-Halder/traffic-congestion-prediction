"""Train a 15-minute-ahead congestion classifier using chronological evaluation."""
import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

FEATURES = [
    "current_speed", "free_flow_speed", "speed_ratio",
    "traffic_confidence", "temperature", "humidity", "rain_1h",
    "hour", "day_of_week",
]
LABELS = ["Low", "Moderate", "Heavy"]
HORIZON_MINUTES = 15
TOLERANCE_MINUTES = 5


def prepare_data(csv_path, horizon_minutes=HORIZON_MINUTES,
                 tolerance_minutes=TOLERANCE_MINUTES):
    """Pair each reading with the same road's reading 15 (+/-5) minutes later."""
    df = pd.read_csv(csv_path)
    required = ["timestamp_utc", "location_id", "current_speed_kmph",
                "free_flow_speed_kmph", "confidence", "temperature_c",
                "humidity_pct", "rain_1h_mm"]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing training columns: {missing}")
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df["location_id"] = df["location_id"].astype("string").str.strip().replace("", pd.NA)
    df = df.dropna(subset=["timestamp_utc", "location_id"]).copy()
    for col in required[2:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["current_speed_kmph"] < 0, "current_speed_kmph"] = np.nan
    df.loc[df["free_flow_speed_kmph"] <= 0, "free_flow_speed_kmph"] = np.nan
    df.loc[~df["confidence"].between(0, 1), "confidence"] = np.nan
    df.loc[~df["humidity_pct"].between(0, 100), "humidity_pct"] = np.nan
    df.loc[df["rain_1h_mm"] < 0, "rain_1h_mm"] = np.nan
    df = df.sort_values(["location_id", "timestamp_utc"]).drop_duplicates(
        ["location_id", "timestamp_utc"], keep="last").reset_index(drop=True)
    local = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
    df["hour"] = local.dt.hour
    df["day_of_week"] = local.dt.dayofweek
    df["current_speed"] = df["current_speed_kmph"]
    df["free_flow_speed"] = df["free_flow_speed_kmph"]
    df["speed_ratio"] = df["current_speed"] / df["free_flow_speed"]
    df["traffic_confidence"] = df["confidence"]
    df["temperature"] = df["temperature_c"]
    df["humidity"] = df["humidity_pct"]
    df["rain_1h"] = df["rain_1h_mm"]

    valid = df["speed_ratio"].notna() & np.isfinite(df["speed_ratio"])
    df["current_level"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df.loc[valid & (df["speed_ratio"] < 0.70), "current_level"] = "Heavy"
    df.loc[valid & (df["speed_ratio"] >= 0.70) & (df["speed_ratio"] < 0.90),
           "current_level"] = "Moderate"
    df.loc[valid & (df["speed_ratio"] >= 0.90), "current_level"] = "Low"

    # merge_asof matches within each road, never across locations.
    # Using nearest avoids pretending that an arbitrary next observation is 15 min away.
    future = df[["location_id", "timestamp_utc", "current_level"]].dropna(
        subset=["current_level"]).rename(columns={
            "timestamp_utc": "next_time", "current_level": "target",
        }).sort_values("next_time")
    current = df.sort_values("timestamp_utc").copy()
    current["desired_time"] = current["timestamp_utc"] + pd.Timedelta(minutes=horizon_minutes)
    paired = pd.merge_asof(
        current.sort_values("desired_time"), future,
        left_on="desired_time", right_on="next_time",
        by="location_id", direction="nearest",
        tolerance=pd.Timedelta(minutes=tolerance_minutes),
    )
    paired = paired.dropna(subset=["target", "next_time"]).copy()
    # Ensure future label is genuinely later than current reading.
    paired = paired[paired["next_time"] > paired["timestamp_utc"]].copy()
    for col in FEATURES:
        paired[col] = pd.to_numeric(paired[col], errors="coerce").replace(
            [np.inf, -np.inf], np.nan)
    # Do not train on invalid current traffic readings.
    paired = paired.dropna(subset=["current_speed", "free_flow_speed", "speed_ratio"])
    return paired.sort_values(["timestamp_utc", "location_id"]).reset_index(drop=True)


def train(data_path, model_path):
    df = prepare_data(data_path)
    if len(df) < 30:
        raise ValueError(
            f"Only {len(df)} valid 15-minute pairs. Collect more regular observations."
        )
    # Split on observation time, then exclude training rows whose future target
    # occurs at or after the test period starts.
    timestamps = df["timestamp_utc"].drop_duplicates().sort_values()
    if len(timestamps) < 2:
        raise ValueError("Need observations at multiple timestamps")
    split_time = timestamps.iloc[int(len(timestamps) * 0.8)]
    train_df = df[(df["timestamp_utc"] < split_time) &
                  (df["next_time"] < split_time)].copy()
    test_df = df[df["timestamp_utc"] >= split_time].copy()
    if train_df.empty or test_df.empty:
        raise ValueError("Not enough data for leakage-free chronological split")
    if train_df["target"].nunique() < 2:
        raise ValueError("Training data needs at least two congestion classes")
    if train_df[FEATURES].notna().sum().eq(0).any():
        raise ValueError("A feature is entirely missing in training data")

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight="balanced",
            n_jobs=-1,
        )),
    ])
    model.fit(train_df[FEATURES], train_df["target"])
    predicted = model.predict(test_df[FEATURES])
    print("Training rows:", len(train_df), "Testing rows:", len(test_df))
    print("Prediction horizon:", HORIZON_MINUTES, "+/-", TOLERANCE_MINUTES, "minutes")
    print("Accuracy:", round(accuracy_score(test_df["target"], predicted), 3))
    print("Macro F1:", round(f1_score(test_df["target"], predicted,
                                     labels=LABELS, average="macro", zero_division=0), 3))
    print("Majority baseline:", round(test_df["target"].eq(
        train_df["target"].mode().iloc[0]).mean(), 3))
    print("Confusion matrix (rows=true, columns=predicted):", LABELS)
    print(confusion_matrix(test_df["target"], predicted, labels=LABELS))
    print(classification_report(test_df["target"], predicted,
                                labels=LABELS, zero_division=0))
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": model, "features": FEATURES,
        "labels": LABELS, "horizon_minutes": HORIZON_MINUTES,
        "tolerance_minutes": TOLERANCE_MINUTES,
    }, model_path)
    print("Model saved:", model_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/kolkata_traffic_weather_clean.csv")
    parser.add_argument("--model", default="backend/ml/artifacts/congestion_model.joblib")
    args = parser.parse_args()
    train(args.data, args.model)
