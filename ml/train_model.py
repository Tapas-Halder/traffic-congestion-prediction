from pathlib import Path
import argparse
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from sklearn.pipeline import Pipeline

FEATURES = [
    "current_speed", "free_flow_speed", "speed_ratio",
    "traffic_confidence", "temperature", "humidity",
    "rain_1h", "hour", "day_of_week",
]


def prepare_data(csv_path):
    df = pd.read_csv(csv_path)

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], utc=True, errors="coerce"
    )
    df = df.dropna(
        subset=["timestamp_utc", "location_id"]
    ).copy()

    # Convert timestamp to Kolkata local time.
    local = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
    df["hour"] = local.dt.hour
    df["day_of_week"] = local.dt.dayofweek

    df["current_speed"] = df["current_speed_kmph"]
    df["free_flow_speed"] = df["free_flow_speed_kmph"]
    df["speed_ratio"] = (
        df["current_speed"] /
        df["free_flow_speed"].where(df["free_flow_speed"] > 0)
    )
    df["traffic_confidence"] = df["confidence"]
    df["temperature"] = df["temperature_c"]
    df["humidity"] = df["humidity_pct"]
    df["rain_1h"] = df["rain_1h_mm"]

    # Rule-based congestion labels.
    ratio = df["speed_ratio"]
    df["current_level"] = "Heavy"
    df.loc[ratio >= 0.70, "current_level"] = "Moderate"
    df.loc[ratio >= 0.90, "current_level"] = "Low"

    df = df.sort_values(["location_id", "timestamp_utc"])

    # Current features -> next observation's class.
    grouped = df.groupby("location_id")
    df["target"] = grouped["current_level"].shift(-1)
    df["next_time"] = grouped["timestamp_utc"].shift(-1)

    df = df.dropna(subset=["target", "next_time"]).copy()

    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        median = df[col].median()
        df[col] = df[col].fillna(
            0 if pd.isna(median) else median
        )

    return df.sort_values("timestamp_utc")


def train(data_path, model_path):
    df = prepare_data(data_path)

    if len(df) < 30:
        raise ValueError(
            "Too little training data. Collect more observations."
        )

    # Chronological split: older data trains, newer data tests.
    cutoff = df["timestamp_utc"].quantile(0.80)
    train_df = df[df["timestamp_utc"] <= cutoff]
    test_df = df[df["timestamp_utc"] > cutoff]

    if train_df.empty or test_df.empty:
        raise ValueError("Unable to create train/test split.")

    if train_df["target"].nunique() < 2:
        raise ValueError("Training data needs at least two classes.")

    model = Pipeline([
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced",
        ))
    ])

    model.fit(train_df[FEATURES], train_df["target"])
    predictions = model.predict(test_df[FEATURES])

    print("Training rows:", len(train_df))
    print("Testing rows:", len(test_df))
    print(
        "Accuracy:",
        round(accuracy_score(test_df["target"], predictions), 3),
    )
    print(classification_report(
        test_df["target"], predictions, zero_division=0
    ))

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump({
        "pipeline": model,
        "features": FEATURES,
    }, model_path)

    print("Model saved:", model_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        default="data/processed/kolkata_traffic_weather_clean.csv",
    )
    parser.add_argument(
        "--model",
        default="ml/artifacts/congestion_model.joblib",
    )
    args = parser.parse_args()
    train(args.data, args.model)