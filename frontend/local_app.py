"""Local offline Streamlit entrypoint. No backend or external APIs are used."""
from __future__ import annotations

import os
import runpy
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent

# The local version must never call FastAPI, TomTom, OpenWeather or map tile servers.
os.environ["TRAFFICIQ_OFFLINE_MODE"] = "1"

st.set_page_config(page_title="TrafficIQ | Offline", page_icon="🚦", layout="wide")

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ — Offline PC")
    mode = st.radio(
        "Choose an offline feature",
        [
            "📊 Kolkata saved historical data",
            "📁 Upload your own CSV",
        ],
        index=0,
    )
    st.caption("Uses only files and ML model stored on this computer. No internet/API required after setup.")

st.session_state["use_default_historical_csv"] = mode.startswith("📊")
runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
