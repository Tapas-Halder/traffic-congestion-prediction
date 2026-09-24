import os
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/"backend/.env")
APP_NAME="Traffic Congestion Prediction API"
TOMTOM_API_KEY=os.getenv("TOMTOM_API_KEY","")
OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY","")
FRONTEND_URL=os.getenv("FRONTEND_URL","*")
MODEL_PATH=ROOT/"ml/artifacts/traffic_model.joblib"
DEFAULT_LAT=float(os.getenv("DEFAULT_LAT","22.5726"))
DEFAULT_LON=float(os.getenv("DEFAULT_LON","88.3639"))
