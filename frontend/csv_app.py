"""Worldwide CSV visualization and historical 15-minute ML prediction."""
from __future__ import annotations
import io
import sys
from pathlib import Path
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ml.csv_inference import REQUIRED, OPTIONAL, predict_csv
from ml.random_forest_model import MODEL_PATH, load_model

@st.cache_resource(show_spinner="Preparing ML model...")
def ensure_model():
    if not MODEL_PATH.is_file():
        from backend.prepare_model import main
        if not main():
            raise RuntimeError("Could not prepare the ML model from the saved dataset.")
    return load_model()

local = st.session_state.get("trafficiq_local", False)
if local:
    st.title("🚦 TrafficIQ — Local PC")
    st.caption("Offline historical prediction. Internet and FastAPI are not required.")
with st.expander("CSV format and sample"):
    st.code(",".join(REQUIRED + OPTIONAL), language="text")
    sample = pd.DataFrame([{"timestamp_utc":"2026-10-18T10:00:00Z","location_id":"example-road",
        "current_speed_kmph":24,"free_flow_speed_kmph":45,"confidence":0.92,
        "temperature_c":30,"humidity_pct":75,"rain_1h_mm":0,
        "latitude":22.5851,"longitude":88.3468}])
    st.download_button("Download sample CSV", sample.to_csv(index=False), "traffic_template.csv")
uploaded = st.file_uploader("Upload traffic + weather CSV (any city)", type=["csv"])
use_saved = local and st.checkbox("Use saved Kolkata CSV", value=True)
source = uploaded
if source is None and use_saved:
    path = ROOT / "data/raw/kolkata_traffic_weather.csv"
    if path.is_file():
        source = path
if source is None:
    st.info("Upload a CSV to predict traffic 15 minutes after each recorded observation.")
    st.stop()
try:
    with st.spinner("Predicting..."):
        ensure_model()
        predictions, rejected = predict_csv(io.BytesIO(source.getvalue()) if hasattr(source,"getvalue") else source)
except Exception as exc:
    st.error("CSV prediction could not run: " + str(exc))
    st.stop()
if predictions.empty:
    st.warning("No valid observations found.")
    st.stop()
roads = sorted(predictions["location_id"].astype(str).unique())
chosen = st.selectbox("Road / checkpoint", roads)
one = predictions[predictions["location_id"].astype(str).eq(chosen)].sort_values("timestamp_utc").iloc[-1]
st.metric("Predicted traffic (15 min after observation)", str(one["predicted_congestion"]))
st.caption("Observation: " + str(one["timestamp_utc"]) + " • Forecast: " + str(one["prediction_at_utc"]))
st.caption("Historical forecast, NOT current live traffic. Model trained in Kolkata; other cities are experimental.")
with st.expander("All results and download"):
    st.dataframe(predictions, use_container_width=True, hide_index=True)
    st.download_button("Download prediction CSV", predictions.to_csv(index=False),
                       "traffic_15min_predictions.csv", mime="text/csv")
    if not rejected.empty:
        st.warning(str(len(rejected)) + " invalid rows skipped")
        st.download_button("Download rejected rows", rejected.to_csv(index=False), "rejected_rows.csv")
st.subheader("Locations on map")
if {"latitude","longitude"}.issubset(predictions.columns):
    mapped = predictions.dropna(subset=["latitude","longitude"])
    mapped = mapped[mapped["latitude"].between(-90,90) & mapped["longitude"].between(-180,180)]
    if not mapped.empty:
        latest = mapped.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
        center = [float(latest["latitude"].mean()), float(latest["longitude"].mean())]
        m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
        colors = {"Low":"green","Moderate":"orange","Heavy":"red"}
        for _, row in latest.iterrows():
            folium.CircleMarker([float(row["latitude"]),float(row["longitude"])],
                radius=8, color=colors.get(str(row["predicted_congestion"]),"gray"),
                fill=True, tooltip=str(row["location_id"]) + ": " + str(row["predicted_congestion"])).add_to(m)
        st_folium(m, height=380, returned_objects=[], key="global_csv_map")
        st.caption("Map tiles require internet; predicted points are from the CSV, not a live route.")
    else:
        st.info("No valid coordinates to plot.")
else:
    st.info("Add latitude and longitude columns for a worldwide map.")
