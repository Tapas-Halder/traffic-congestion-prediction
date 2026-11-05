"""Public Streamlit Community Cloud entrypoint: CSV upload only.

The public app intentionally does not call FastAPI, Render, TomTom or OpenWeather.
Run frontend/local_app.py on a laptop for local historical/CSV modes.
"""
from __future__ import annotations

import runpy
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
st.set_page_config(
    page_title="TrafficIQ | CSV Traffic Prediction",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

runpy.run_path(str(HERE / "csv_app.py"), run_name="__main__")
