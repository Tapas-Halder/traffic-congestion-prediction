"""Train a next-observation congestion classifier from cleaned Kolkata data.

Run from repository root:
    python ml/train_model.py --data data/processed/kolkata_traffic_weather_clean.csv

The target is the next available observation for the same location, not a guaranteed
15-minute forecast. Use sufficiently frequent historical collection before claiming
a fixed prediction horizon.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUMERIC_FEATURES = [
    "hour", "day_of_week", "latitude", "longitude",
    "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec",
    "confidence", "road_closure", "temperature_c", "feels_like_c",
    "humidity_pct", "pressure_hpa", "wind_speed_mps", "rain_1h_mm",
]
CATEGORICAL_FEATURES = ["location_id", "road_name", "corridor", "weather_main"]
TARGET = "next_congestion_level"


def make_training_frame(csv_path: Path) -> pd.DataFrame:
    """Create time features and next-observation target for each road location."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Clean CSV not found: {csv_path}. Run ml/clean_data.py first."
        )
    df = pd.read_csv(csv_path)
    required = set(
        ["timestamp_utc", "current_speed_kmph", "free_flow_speed_kmph"]
        + NUMERIC_FEATURES + CATEGORICAL_FEATURES
    )
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Clean CSV is missing columns: {missing}")

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp_utc", "location_id"]).copy()
    local_time = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
    df["hour"] = local_time.dt.hour
    df["day_of_week"] = local_time.dt.dayofweek
    df = df.sort_values(["location_id", "timestamp_utc"])

    ratio = df["current_speed_kmph"] / df["free_flow_speed_kmph"].where(
        df["free_flow_speed_kmph"] > 0
    )
    df["observed_congestion_level"] = "Heavy"
    df.loc[ratio >= 0.70, "observed_congestion_level"] = "Moderate"
    df.loc[ratio >= 0.90, "observed_congestion_level"] = "Low"

    # Shift label backwards so current row features predict the next row's label.
    df[TARGET] = df.groupby("location_id")["observed_congestion_level"].shift(-1)
    df["next_timestamp_utc"] = df.groupby("location_id")["timestamp_utc"].shift(-1)
    df = df.dropna(subset=[TARGET, "next_timestamp_utc"]).copy()

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        median = df[column].median()
        df[column] = df[column].fillna(0 if pd.isna(median) else median)
    for column in CATEGORICAL_FEATURES:
        df[column] = df[column].fillna("Unknown").astype(str)
    df["road_closure"] = df["road_closure"].map(
        {True: 1, False: 0, "True": 1, "False": 0, 1: 1, 0: 0}
    ).fillna(0).astype(int)
    return df.sort_values("timestamp_utc").reset_index(drop=True)


def train(data_path: Path, model_path: Path) -> None:
    """Train with a chronological split, print metrics, and save the model bundle."""
    df = make_training_frame(data_path)
    if len(df) < 30:
        raise ValueError(
            f"Only {len(df)} labelled rows available. Collect more observations before training."
        )

    cutoff = df["timestamp_utc"].quantile(0.80)
    train_df = df[df["timestamp_utc"] <= cutoff]
    test_df = df[df["timestamp_utc"] > cutoff]
    if train_df.empty or test_df.empty or train_df[TARGET].nunique() < 2:
        raise ValueError("Not enough time-separated examples/classes to train and evaluate.")

    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_train, y_train = train_df[features], train_df[TARGET]
    X_test, y_test = test_df[features], test_df[TARGET]

    prep = ColumnTransformer([
        ("numeric", "passthrough", NUMERIC_FEATURES),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    model = Pipeline([
        ("preprocessing", prep),
        ("classifier", RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight="balanced"
        )),
    ])
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    print(f"Training rows: {len(train_df)} | Test rows: {len(test_df)}")
    print(f"Chronological test accuracy: {accuracy_score(y_test, predicted):.3f}")
    print(classification_report(y_test, predicted, zero_division=0))
    print("Target: next available observation's rule-derived congestion class.")
    print("Do not describe this as a fixed 15-minute forecast unless timestamps support that horizon.")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": model,
        "features": features,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET,
    }, model_path)
    print(f"Saved model: {model_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path,
        default=Path("data/processed/kolkata_traffic_weather_clean.csv")
    )
    parser.add_argument(
        "--model", type=Path,
        default=Path("ml/artifacts/congestion_model.joblib")
    )
    args = parser.parse_args()
    train(args.data, args.model)


if __name__ == "__main__":
    main()
