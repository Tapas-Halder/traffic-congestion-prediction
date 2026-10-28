"""TrafficIQ Option A: standalone CSV prediction, no API or Render required."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.csv_inference import REQUIRED, OPTIONAL, predict_csv
from ml.random_forest_model import MODEL_PATH, load_model

st.set_page_config(page_title="TrafficIQ | Kolkata", page_icon="🚦", layout="wide")
st.title("🚦 TrafficIQ — Kolkata")
st.caption("Historical CSV → Random Forest → 15-minute-ahead congestion | No live APIs required")

@st.cache_resource(show_spinner="Preparing trusted historical ML model...")
def ensure_model():
    if not MODEL_PATH.is_file():
        from backend.prepare_model import main as prepare_model
        if not prepare_model():
            raise RuntimeError("Model unavailable: training CSV or required columns missing.")
    return load_model()

with st.expander("Required CSV format", expanded=False):
    st.code(",".join(REQUIRED + OPTIONAL), language="text")
    st.caption("latitude and longitude are optional, but needed for map markers. Timestamps must include UTC or timezone information.")
    example = pd.DataFrame([{
        "timestamp_utc": "2026-10-18T10:00:00Z", "location_id": "H2S-01",
        "current_speed_kmph": 24, "free_flow_speed_kmph": 45,
        "confidence": 0.92, "temperature_c": 30.5, "humidity_pct": 78,
        "rain_1h_mm": 0.0, "latitude": 22.5851, "longitude": 88.3468
    }])
    st.download_button("Download example CSV (illustrative values)", example.to_csv(index=False),
                       "traffic_csv_template.csv", mime="text/csv")

file = st.file_uploader("Upload a CSV with historical Kolkata traffic observations", type=["csv"])
if file is None:
    st.info("Upload a CSV to see predictions. The example CSV is only a format template, not real measured data.")
    st.stop()

try:
    with st.spinner("Loading model and predicting..."):
        ensure_model()
        predictions, rejected = predict_csv(io.BytesIO(file.getvalue()))
except (ValueError, FileNotFoundError, RuntimeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f"Cannot predict: {exc}")
    st.stop()
except Exception:
    st.error("Unexpected prediction error. Check the app logs; no results were generated.")
    st.stop()

if not rejected.empty:
    st.warning(f"{len(rejected)} invalid row(s) skipped.")
    st.dataframe(rejected[["source_row", "error"]], use_container_width=True)
if predictions.empty:
    st.error("No valid rows available for prediction.")
    st.stop()

st.success(f"Predicted {len(predictions)} historical observation(s).")
st.caption("Each result refers to 15 minutes after its own observation timestamp, not 15 minutes from now.")
a, b, c = st.columns(3)
a.metric("Valid rows", len(predictions))
b.metric("Rejected rows", len(rejected))
c.metric("Prediction horizon", "15 minutes")
roads = sorted(predictions["location_id"].astype(str).unique())
selected = st.multiselect("Filter roads", roads, default=roads)
shown = predictions[predictions["location_id"].isin(selected)].copy()
st.subheader("Prediction results")
st.dataframe(shown, use_container_width=True, hide_index=True)
st.download_button("Download predictions CSV", predictions.to_csv(index=False),
                   "kolkata_15min_predictions.csv", mime="text/csv")
if not rejected.empty:
    st.download_button("Download invalid row report", rejected.to_csv(index=False),
                       "invalid_rows.csv", mime="text/csv")

st.subheader("Kolkata road checkpoints")
if {"latitude", "longitude"}.issubset(shown.columns):
    mapped = shown.dropna(subset=["latitude", "longitude"])
    mapped = mapped[mapped["latitude"].between(22.0, 23.0) &
                    mapped["longitude"].between(87.5, 89.0)]
    if not mapped.empty:
        # Show the latest uploaded observation per road, not a continuous predicted route.
        latest = mapped.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
        m = folium.Map(location=[22.5726, 88.3639], zoom_start=11, tiles="OpenStreetMap")
        colors = {"Low": "green", "Moderate": "orange", "Heavy": "red"}
        for _, row in latest.iterrows():
            label = str(row["predicted_congestion"])
            folium.CircleMarker(
                location=[float(row["latitude"]), float(row["longitude"])],
                radius=9, color=colors.get(label, "gray"), fill=True,
                fill_opacity=0.8,
                tooltip=f"{row['location_id']}: {label} at {row['prediction_at_utc']}",
            ).add_to(m)
        st_folium(m, width=None, height=430, returned_objects=[])
        st.caption("Colored points are predicted checkpoint conditions, not road-wide route forecasts.")
    else:
        st.info("No usable Kolkata coordinates in selected rows.")
else:
    st.info("Add latitude and longitude columns to display checkpoints on the map.")

st.divider()
st.caption("Offline historical prediction • TomTom/OpenWeather are not called • "
           "Model probability is not a calibrated reliability guarantee.")
