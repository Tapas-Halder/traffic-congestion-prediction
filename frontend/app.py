"""Simple public TrafficIQ interface. Kolkata live prediction + worldwide CSV uploads."""
from __future__ import annotations
import os
import runpy
from pathlib import Path
import streamlit as st
from traffic_core import call_backend, parse_prediction, prediction_label

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ | 15-minute traffic", page_icon="🚦", layout="wide")
st.title("🚦 TrafficIQ")
st.caption("Next 15-minute traffic condition • Kolkata by default")
st.info("Live prediction uses Kolkata traffic/weather through FastAPI. Upload CSV to explore historical observations from other cities.")
tab_live, tab_upload = st.tabs(["🚦 Next 15 minutes", "📂 Upload city CSV"])
LOCATIONS = {
    "Esplanade": (22.5646, 88.3510),
    "Park Street": (22.5535, 88.3520),
    "Howrah Bridge": (22.5851, 88.3468),
    "EM Bypass": (22.5395, 88.3960),
    "Salt Lake": (22.5726, 88.4338),
}
def setting(key, default):
    if os.environ.get(key):
        return os.environ[key]
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default
backend = str(setting("BACKEND_URL", "https://kolkata-traffic-api.onrender.com")).rstrip("/")
with tab_live:
    st.subheader("Kolkata — 15 minutes ahead")
    location = st.selectbox("Choose a Kolkata location", list(LOCATIONS))
    st.caption("Real-time data may be unavailable when Render sleeps or external API quota is exhausted.")
    if st.button("Predict traffic", type="primary", use_container_width=True):
        lat, lon = LOCATIONS[location]
        with st.spinner("Getting current traffic and weather..."):
            response = call_backend(backend, "POST", "/api/v1/predict",
                                    json_body={"location": location, "latitude": lat, "longitude": lon},
                                    timeout=90)
        if response["ok"]:
            pred = parse_prediction(response["data"])
            label = prediction_label(pred["prediction"])
            if label:
                st.metric("Traffic in the next 15 minutes", label)
                st.caption("Location: " + location + " • ML estimate, not a guarantee")
                reported = pred.get("location")
                if reported and isinstance(reported, str) and location.lower() not in reported.lower():
                    st.warning("Backend reported another location: " + reported)
                with st.expander("Technical details"):
                    st.json(response["data"])
            else:
                st.error("Backend responded but no prediction was returned.")
        else:
            st.error("Prediction unavailable: " + response["error"]["message"])
            st.caption("Try again later, or use CSV upload for historical predictions.")
with tab_upload:
    st.caption("Worldwide CSV support: latitude/longitude determine map location. No TomTom or OpenWeather calls are made for uploaded rows.")
    st.warning("The current Random Forest was trained on Kolkata data. Results for other cities are experimental and not validated for those cities.")
    runpy.run_path(str(ROOT / "csv_app.py"), run_name="__main__")
