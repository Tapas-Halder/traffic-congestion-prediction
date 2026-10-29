"""Local-only Streamlit entrypoint; never used by Streamlit Community Cloud."""
import runpy
from pathlib import Path
import streamlit as st
st.set_page_config(page_title="TrafficIQ Local", page_icon="🚦", layout="wide")
st.session_state["trafficiq_local"] = True
st.caption("Local PC edition • Saved Kolkata data or worldwide CSV • no FastAPI required")
runpy.run_path(str(Path(__file__).resolve().parent / "csv_app.py"), run_name="__main__")
