"""TrafficIQ launcher: restore the full original dashboard and add CSV as a separate feature.

Use the original FastAPI/Render dashboard online or with a locally running FastAPI.
CSV mode runs directly on the local machine or Streamlit Cloud without FastAPI.
"""
from __future__ import annotations

import os
import runpy
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ — Kolkata", page_icon="🚦", layout="wide",
                   initial_sidebar_state="expanded")

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    feature = st.radio(
        "Dashboard feature",
        ["Original dashboard (FastAPI + Render)", "CSV upload (local ML, no API)"],
        index=0,
        help="Original preserves Overview, Roads, Map, Route, Pipeline and Kolkata locations. CSV is additional.",
    )

if feature.startswith("Original"):
    # The original dashboard uses its existing backend routes, locations and charts.
    # Default URL supports the deployed Render service; override for local FastAPI.
    os.environ.setdefault("BACKEND_URL", "https://kolkata-traffic-api.onrender.com")
    runpy.run_path(str(ROOT / "legacy_live_app.py"), run_name="__main__")
else:
    runpy.run_path(str(ROOT / "csv_app.py"), run_name="__main__")
