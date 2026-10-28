"""Evaluate saved Random Forest on the held-out chronological test period."""
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, classification_report
from ml.train_model import prepare_data, FEATURES, LABELS

root = Path(__file__).resolve().parents[1]
data = prepare_data(root / "data/processed/kolkata_traffic_weather_clean.csv")
timestamps = data["timestamp_utc"].drop_duplicates().sort_values()
split_time = timestamps.iloc[int(len(timestamps) * 0.8)]
train = data[(data["timestamp_utc"] < split_time) & (data["next_time"] < split_time)]
test = data[data["timestamp_utc"] >= split_time]
if train.empty or test.empty:
    raise ValueError("Chronological split has no training or test observations")
artifact = joblib.load(root / "ml/artifacts/congestion_model.joblib")
prediction = artifact["pipeline"].predict(test[FEATURES])
actual = test["target"]
result = {
    "status": "measured",
    "horizon_minutes": 15,
    "tolerance_minutes": 5,
    "cleaned_rows": int(len(pd.read_csv(root / "data/processed/kolkata_traffic_weather_clean.csv"))),
    "valid_future_pairs": int(len(data)),
    "training_rows": int(len(train)),
    "testing_rows": int(len(test)),
    "test_start_utc": str(split_time),
    "accuracy": float(accuracy_score(actual, prediction)),
    "macro_precision": float(precision_score(actual, prediction, labels=LABELS, average="macro", zero_division=0)),
    "macro_recall": float(recall_score(actual, prediction, labels=LABELS, average="macro", zero_division=0)),
    "macro_f1": float(f1_score(actual, prediction, labels=LABELS, average="macro", zero_division=0)),
    "majority_baseline_accuracy": float(actual.eq(train["target"].mode().iloc[0]).mean()),
    "label_order": LABELS,
    "confusion_matrix": confusion_matrix(actual, prediction, labels=LABELS).tolist(),
    "classification_report": classification_report(actual, prediction, labels=LABELS, output_dict=True, zero_division=0),
    "training_class_counts": {str(k): int(v) for k, v in train["target"].value_counts().items()},
    "testing_class_counts": {str(k): int(v) for k, v in test["target"].value_counts().items()},
}
path = root / "documentation/ML_EVALUATION_RESULTS.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
