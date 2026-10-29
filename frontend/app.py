"""TrafficIQ — one simple public dashboard, plus global CSV prediction.

Public Streamlit Cloud: Kolkata dashboard and CSV upload only.
Local installation: launch local_app.py for historical offline use.
Developer: set BACKEND_URL to a local FastAPI URL before running this app.
"""
from __future__ import annotations

import os
import runpy
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ | Next 15 Minutes", page_icon="🚦",
                   layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Next 15-minute traffic condition")
    page = st.radio("What would you like to see?",
                    ["🗺️ Traffic dashboard", "📁 Predict from CSV"],
                    index=0, label_visibility="collapsed")
    st.caption("Default city: Kolkata · Upload traffic observations from other cities in CSV.")

if page.startswith("🗺️"):
    os.environ.setdefault("BACKEND_URL", "https://kolkata-traffic-api.onrender.com")
    runpy.run_path(str(HERE / "legacy_live_app.py"), run_name="__main__")
else:
    st.session_state["use_default_historical_csv"] = False
    runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
