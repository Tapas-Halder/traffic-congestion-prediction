"""Local-only Streamlit entrypoint. Never configure this file as Cloud main file."""
from __future__ import annotations
import os
import runpy
from pathlib import Path
import streamlit as st

HERE = Path(__file__).resolve().parent
st.set_page_config(page_title="TrafficIQ | Local", page_icon="🚦", layout="wide")
with st.sidebar:
    st.markdown("## 🚦 TrafficIQ — Local PC")
    mode = st.radio("Local feature", [
        "📊 Kolkata saved data (no internet)",
        "📁 Upload city CSV (no API needed)",
        "🗺️ Full dashboard (backend required)",
    ])
    st.caption("This launcher is for installation on your own computer, not the public website.")

if mode.startswith("🗺️"):
    os.environ.setdefault("BACKEND_URL", "http://127.0.0.1:8000")
    runpy.run_path(str(HERE / "legacy_live_app.py"), run_name="__main__")
else:
    st.session_state["use_default_historical_csv"] = mode.startswith("📊")
    runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
