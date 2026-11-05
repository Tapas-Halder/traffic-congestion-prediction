"""TrafficIQ public Streamlit entrypoint.

The dashboard page calls the deployed FastAPI backend for live Kolkata data.
The CSV page runs the repository's Python ML model against an uploaded CSV.
No API credentials are stored in Streamlit or the repository.
"""
from pathlib import Path
import streamlit as st

HERE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="TrafficIQ | Kolkata Traffic Prediction",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "Live Kolkata": [
        st.Page(
            str(HERE / "legacy_live_app.py"),
            title="Live Kolkata Dashboard",
            icon="🚦",
            default=True,
        ),
    ],
    "CSV Prediction": [
        st.Page(
            str(HERE / "pages" / "2_CSV_Upload.py"),
            title="CSV Upload Prediction",
            icon="📄",
        ),
    ],
}

navigation = st.navigation(pages, position="sidebar")
navigation.run()
