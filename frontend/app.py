"""TrafficIQ: original Kolkata dashboard plus one optional CSV analysis page."""
from __future__ import annotations

import os
import runpy
from pathlib import Path
import streamlit as st

HERE = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ — Kolkata", page_icon="🚦",
                   layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    page = st.radio("Go to", ["🏠 Kolkata Dashboard", "📁 CSV Prediction"], index=0,
                    help="Dashboard includes your existing live/offline controls and Kolkata route. CSV is an extra tool.")
    st.caption("Kolkata Traffic Congestion Prediction")

if page == "🏠 Kolkata Dashboard":
    os.environ.setdefault("BACKEND_URL", "https://kolkata-traffic-api.onrender.com")
    runpy.run_path(str(HERE / "legacy_live_app.py"), run_name="__main__")
else:
    runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
