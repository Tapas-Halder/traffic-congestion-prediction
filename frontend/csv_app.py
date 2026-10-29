"""Simple CSV analysis page. Historical predictions, not live traffic."""
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

LABELS = {"Low": "🟢 Low — Light traffic",
          "Moderate": "🟠 Moderate — Some traffic",
          "Heavy": "🔴 Heavy — Traffic jam"}
COLORS = {"Low": "green", "Moderate": "orange", "Heavy": "red"}

st.title("📁 CSV Traffic Prediction")
st.write("See **simple 15-minute-ahead predictions** using real historical Kolkata traffic data.")
st.info("📅 These results are based on the timestamp of each CSV reading — **not current/live traffic**.")

@st.cache_resource(show_spinner="Preparing the saved Random Forest model…")
def ensure_model():
    if not MODEL_PATH.is_file():
        from backend.prepare_model import main as prepare_model
        if not prepare_model():
            raise RuntimeError("Model preparation failed. Check the saved historical dataset.")
    return load_model()

uploaded = st.file_uploader("Optional: upload your own traffic CSV", type=["csv"],
                            help="Leave empty to use the existing Kolkata historical dataset.")
source = uploaded
if source is None:
    source = ROOT / "data/raw/kolkata_traffic_weather.csv"
    if not source.is_file():
        st.error("Default Kolkata historical CSV not found. Upload a CSV to continue.")
        st.stop()
    st.caption("Using the saved Kolkata historical CSV. You can upload another file instead.")
else:
    st.caption("Using your uploaded CSV.")

with st.expander("CSV format / sample file"):
    st.code(",".join(REQUIRED + OPTIONAL), language="text")
    sample = pd.DataFrame([{
        "timestamp_utc": "2026-10-18T10:00:00Z", "location_id": "H2S-01",
        "current_speed_kmph": 24, "free_flow_speed_kmph": 45,
        "confidence": 0.92, "temperature_c": 30.5, "humidity_pct": 78,
        "rain_1h_mm": 0.0, "latitude": 22.5851, "longitude": 88.3468
    }])
    st.download_button("Download sample format", sample.to_csv(index=False),
                       "traffic_csv_template.csv", mime="text/csv")

try:
    with st.spinner("Calculating traffic predictions…"):
        ensure_model()
        source_data = io.BytesIO(uploaded.getvalue()) if uploaded is not None else source
        predictions, rejected = predict_csv(source_data)
except (ValueError, FileNotFoundError, RuntimeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f"Could not calculate predictions: {exc}")
    st.stop()
except Exception:
    st.error("Prediction failed unexpectedly. See Streamlit logs.")
    st.stop()

if predictions.empty:
    st.error("No valid traffic observations were found.")
    if not rejected.empty:
        with st.expander("Invalid CSV rows"):
            st.dataframe(rejected[["source_row", "error"]], hide_index=True)
    st.stop()

# One simple result per checkpoint: newest historical reading in the supplied CSV.
latest = (predictions.sort_values(["timestamp_utc", "source_row"])
          .drop_duplicates("location_id", keep="last")
          .sort_values("location_id").copy())
roads = sorted(latest["location_id"].astype(str).unique())
selected = st.selectbox("📍 Choose a Kolkata checkpoint", roads)
one = latest[latest["location_id"].astype(str) == selected].iloc[0]
level = str(one["predicted_congestion"])
st.subheader("Your traffic prediction")
st.markdown(f"### {LABELS.get(level, level)}")
time_ist = pd.Timestamp(one["prediction_at_utc"]).tz_convert("Asia/Kolkata")
st.write(f"**Checkpoint:** {selected}")
st.write(f"**Prediction for:** {time_ist.strftime('%d %b %Y, %I:%M %p')} IST")
st.caption("15 minutes after the recorded observation. This is a model estimate, not a confirmed future condition.")

count_low = int((latest["predicted_congestion"] == "Low").sum())
count_mid = int((latest["predicted_congestion"] == "Moderate").sum())
count_high = int((latest["predicted_congestion"] == "Heavy").sum())
st.subheader("Latest prediction for each checkpoint")
c1, c2, c3 = st.columns(3)
c1.metric("🟢 Low", count_low)
c2.metric("🟠 Moderate", count_mid)
c3.metric("🔴 Heavy", count_high)
simple = latest[["location_id", "prediction_at_utc", "predicted_congestion"]].copy()
simple.columns = ["Checkpoint", "Prediction time (UTC)", "Traffic level"]
simple["Traffic level"] = simple["Traffic level"].map(LABELS).fillna(simple["Traffic level"])
st.dataframe(simple, use_container_width=True, hide_index=True)

if {"latitude", "longitude"}.issubset(latest.columns):
    mapped = latest.dropna(subset=["latitude", "longitude"])
    mapped = mapped[mapped["latitude"].between(22.0, 23.0) &
                    mapped["longitude"].between(87.5, 89.0)]
    if not mapped.empty:
        st.subheader("🗺️ Kolkata checkpoint map")
        m = folium.Map(location=[22.5726, 88.3639], zoom_start=11, tiles="OpenStreetMap")
        for _, row in mapped.iterrows():
            traffic = str(row["predicted_congestion"])
            folium.CircleMarker(
                [float(row["latitude"]), float(row["longitude"])],
                radius=9, color=COLORS.get(traffic, "gray"), fill=True,
                fill_opacity=0.8,
                tooltip=f"{row['location_id']} — {traffic}",
            ).add_to(m)
        st_folium(m, height=390, returned_objects=[], key="csv_simple_map")
        st.caption("Dots show predicted conditions at sampled checkpoints, not full road routes.")

st.download_button("⬇️ Download all predictions", predictions.to_csv(index=False),
                   "kolkata_15min_predictions.csv", mime="text/csv")
with st.expander("Advanced details (optional)"):
    st.caption(f"{len(predictions)} valid rows • {len(rejected)} skipped rows • 15-minute prediction horizon")
    st.caption("Model probability is not a guarantee of correctness.")
    st.dataframe(predictions, use_container_width=True, hide_index=True)
    if not rejected.empty:
        st.warning(f"{len(rejected)} invalid rows skipped.")
        st.dataframe(rejected[["source_row", "error"]], use_container_width=True, hide_index=True)
        st.download_button("Download invalid rows", rejected.to_csv(index=False),
                           "invalid_rows.csv", mime="text/csv")
st.caption("Original Kolkata dashboard, live FastAPI prediction, and road routes are available under 🏠 Kolkata Dashboard.")
