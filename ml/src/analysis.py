"""Descriptive statistics for the actual collected Kolkata observations."""
from ml.src.data_loader import load_csv

def summarize_data(path):
    df = load_csv(path)
    return {"rows": int(len(df)), "columns": list(df.columns),
            "locations": int(df["location_id"].nunique()) if "location_id" in df else None,
            "first_timestamp": str(df["timestamp_utc"].min()) if "timestamp_utc" in df and len(df) else None,
            "last_timestamp": str(df["timestamp_utc"].max()) if "timestamp_utc" in df and len(df) else None}
