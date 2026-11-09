"""TrafficIQ: standalone CSV prediction; no API or FastAPI calls."""
from __future__ import annotations

import io
import os
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

OFFLINE_MODE = os.getenv("TRAFFICIQ_OFFLINE_MODE", "").strip() == "1"
MAP_TILES = None if OFFLINE_MODE else "OpenStreetMap"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp{background:radial-gradient(ellipse at 15% 0%,#142c49 0%,#08111f 45%,#070d18 100%);color:#edf5ff;font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#101d30;border-right:1px solid #263850}
.block-container{max-width:1400px;padding-top:2rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;color:#f3f8ff;letter-spacing:-.03em}
h1{font-size:2.25rem!important}
p,label{color:#a9bad0}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#17283e,#101c2d);border:1px solid #2a405b;padding:15px;border-radius:15px}
div[data-testid="stMetricValue"]{color:#f3f8ff;font-family:'Space Grotesk',sans-serif}
.stButton>button,.stDownloadButton>button{border-radius:10px;background:linear-gradient(110deg,#1768b4,#258fc4);border:1px solid #3977b7;color:white;font-weight:700;min-height:42px}
.stAlert{border-radius:12px}
[data-testid="stDataFrame"]{border:1px solid #263850;border-radius:12px;overflow:hidden}
</style>
""", unsafe_allow_html=True)

st.title("🚦 TrafficIQ — CSV Prediction")
st.caption("Upload traffic observations · Prediction target: 15 minutes after each observation")
st.warning("The ML model was trained on Kolkata data. Predictions for other cities are experimental and not locally validated.")

@st.cache_resource(show_spinner="Preparing the local ML model...")
def ensure_model():
    if not MODEL_PATH.is_file():
        # This trains from the historical CSV bundled in the repository. It makes no API calls.
        from backend.prepare_model import main as prepare_model
        if not prepare_model():
            raise RuntimeError("Model unavailable: bundled historical CSV or required columns are missing.")
    return load_model()

with st.expander("Required CSV format", expanded=False):
    st.code(",".join(REQUIRED + OPTIONAL), language="text")
    st.caption("latitude and longitude are optional. Timestamps must include UTC or timezone information.")
    example = pd.DataFrame([{
        "timestamp_utc": "2026-10-18T10:00:00Z", "location_id": "H2S-01",
        "current_speed_kmph": 24, "free_flow_speed_kmph": 45,
        "confidence": 0.92, "temperature_c": 30.5, "humidity_pct": 78,
        "rain_1h_mm": 0.0, "latitude": 22.5851, "longitude": 88.3468, "time_zone": "Asia/Kolkata"
    }])
    st.download_button("Download example CSV (illustrative values)", example.to_csv(index=False),
                       "traffic_csv_template.csv", mime="text/csv")

file = st.file_uploader("Upload traffic CSV", type=["csv"])
if file is None and st.session_state.get("use_default_historical_csv", False):
    historical = ROOT / "data/raw/kolkata_traffic_weather.csv"
    if historical.is_file():
        file = historical
        st.info("Using the bundled real Kolkata historical dataset. Upload another CSV to replace it.")
    else:
        st.error("Bundled historical CSV is missing.")
        st.stop()
if file is None:
    st.info("Upload a CSV to generate predictions.")
    st.stop()

try:
    with st.spinner("Loading model and predicting..."):
        ensure_model()
        predictions, rejected = predict_csv(io.BytesIO(file.getvalue()) if hasattr(file, "getvalue") else file)
except (ValueError, FileNotFoundError, RuntimeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f"Cannot predict: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Prediction failed ({type(exc).__name__}). Check the local terminal for details.")
    st.stop()

if not rejected.empty:
    st.warning(f"{len(rejected)} invalid row(s) skipped.")
    st.dataframe(rejected[["source_row", "error"]], use_container_width=True)
if predictions.empty:
    st.error("No valid rows available for prediction.")
    st.stop()

st.success(f"Predicted {len(predictions)} observation(s).")
st.caption("Each result is for 15 minutes after its own input timestamp, not 15 minutes from the current clock time.")
a, b, c = st.columns(3)
a.metric("Valid rows", len(predictions))
b.metric("Rejected rows", len(rejected))
c.metric("Prediction horizon", "15 minutes")
roads = sorted(predictions["location_id"].astype(str).unique())
selected = st.multiselect("Filter roads", roads, default=roads)
shown = predictions[predictions["location_id"].isin(selected)].copy()

st.subheader("🚦 Predicted traffic condition")
latest_by_road = shown.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
if not latest_by_road.empty:
    for _, item in latest_by_road.head(12).iterrows():
        st.markdown(f"**{item['location_id']}** — **{item['predicted_congestion']}** · observed: {item['timestamp_utc']} · target: {item['prediction_at_utc']}")

with st.expander("See all prediction rows"):
    st.dataframe(shown, use_container_width=True, hide_index=True)
st.download_button("Download predictions CSV", predictions.to_csv(index=False),
                   "traffic_15min_predictions.csv", mime="text/csv")
if not rejected.empty:
    st.download_button("Download invalid row report", rejected.to_csv(index=False),
                       "invalid_rows.csv", mime="text/csv")

st.subheader("🗺️ Traffic checkpoint map")
if {"latitude", "longitude"}.issubset(shown.columns):
    mapped = shown.dropna(subset=["latitude", "longitude"])
    mapped = mapped[mapped["latitude"].between(-90, 90) &
                    mapped["longitude"].between(-180, 180)]
    if not mapped.empty:
        latest = mapped.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
        m = folium.Map(
            location=[float(latest["latitude"].mean()), float(latest["longitude"].mean())],
            zoom_start=10,
            tiles=MAP_TILES,
        )
        colors = {"Low": "green", "Moderate": "orange", "Heavy": "red"}
        for _, row in latest.iterrows():
            label = str(row["predicted_congestion"])
            folium.CircleMarker(
                location=[float(row["latitude"]), float(row["longitude"])],
                radius=9, color=colors.get(label, "gray"), fill=True,
                fill_opacity=0.8,
                tooltip=f"{row['location_id']}: {label} at {row['prediction_at_utc']}",
            ).add_to(m)
        if len(latest) > 1:
            m.fit_bounds(latest[["latitude", "longitude"]].values.tolist())
        st_folium(m, width=None, height=430, returned_objects=[])
        if OFFLINE_MODE:
            st.caption("Offline map: prediction points are shown without online background map tiles.")
        else:
            st.caption("Colored points show predicted checkpoint conditions, not road-wide route forecasts.")
    else:
        st.info("No valid coordinates were provided in the selected CSV rows.")
else:
    st.info("Add latitude and longitude columns to your CSV to display checkpoint locations.")

st.divider()
st.caption("CSV prediction · No TomTom, OpenWeather or FastAPI calls · Model probability is not a calibrated reliability guarantee.")
