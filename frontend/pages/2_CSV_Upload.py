"""Streamlit multipage wrapper for the standalone CSV prediction app."""
from pathlib import Path
import runpy

FRONTEND_DIR = Path(__file__).resolve().parents[1]
runpy.run_path(str(FRONTEND_DIR / "csv_app.py"), run_name="__main__")
