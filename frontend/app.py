"""TrafficIQ public dashboard and opt-in local-only development workspace.

Public Streamlit Cloud: Kolkata live dashboard + global historical CSV.
Local install: explicitly set TRAFFICIQ_LOCAL_MODE=1 to unlock offline and dev tools.
"""
from __future__ import annotations

import os
import runpy
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ | Traffic Prediction", page_icon="🚦",
                   layout="wide", initial_sidebar_state="expanded")

# Streamlit Community Cloud is public; local-only options require an explicit
# setting on a developer's own machine, not a public-facing toggle.
local_mode = os.environ.get("TRAFFICIQ_LOCAL_MODE", "").lower() in ("1", "true", "yes")
with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Kolkata live traffic • Worldwide CSV analysis")
    if local_mode:
        choice = st.radio("Choose a task", [
            "Live traffic (Kolkata)",
            "Upload traffic CSV (any city)",
            "Offline Kolkata sample",
            "Developer: local FastAPI",
        ], label_visibility="collapsed")
        st.caption("Local installation • development tools enabled")
    else:
        choice = st.radio("Choose a task", [
            "Live traffic (Kolkata)",
            "Upload traffic CSV (any city)",
        ], label_visibility="collapsed")
    st.divider()

if choice in ("Live traffic (Kolkata)", "Developer: local FastAPI"):
    if choice == "Developer: local FastAPI":
        os.environ["BACKEND_URL"] = os.environ.get("TRAFFICIQ_DEV_BACKEND_URL", "http://127.0.0.1:8000")
    else:
        os.environ.setdefault("BACKEND_URL", "https://kolkata-traffic-api.onrender.com")
    runpy.run_path(str(HERE / "legacy_live_app.py"), run_name="__main__")
else:
    st.session_state["use_default_historical_csv"] = choice == "Offline Kolkata sample"
    runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
