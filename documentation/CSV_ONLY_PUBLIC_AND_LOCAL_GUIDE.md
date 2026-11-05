# CSV-only public website and offline laptop guide

## Public website: CSV upload only

The public Streamlit Community Cloud entry point is `frontend/app.py`. It launches only `frontend/csv_app.py`. It does not call FastAPI, Render, TomTom or OpenWeather. Deploy from the team leader repository after merging the deployment PR:

- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main`
- Main file: `frontend/app.py`
- Requirements: `frontend/requirements.txt`
- No API keys or `BACKEND_URL` Streamlit secrets are needed for CSV prediction.

The public app needs the trained model. If the artifact is missing, it trains from `data/raw/kolkata_traffic_weather.csv`; that file must be present and non-empty in the deployed branch. First startup may take longer.

## Laptop: offline CSV/historical prediction

```powershell
git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git
cd traffic-congestion-prediction
git switch main
git pull origin main
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/local_app.py
```

Choose **Kolkata saved data** or **Upload city CSV**. These modes use local files and the local ML model; no website, FastAPI, Render or external API is called. Internet is needed for the initial Git clone and package installation. After all required files/packages are on the laptop, inference works without internet. OpenStreetMap background tiles will not load offline.

## Optional API collection

TomTom/OpenWeather collection is a separate online process. It requires internet, valid API keys and a running local FastAPI server. It is not required for the public CSV website or local historical CSV prediction.

## CSV input format

Required headers (case-sensitive):

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional: `latitude`, `longitude`, `time_zone`. Each prediction is for 15 minutes after the observation timestamp in that CSV row. The Random Forest was trained on Kolkata data; other-city results are experimental and not locally validated.

## Model quality warning

The recorded test accuracy (60.22%) is below the majority-class baseline (79.77%). Show the evaluation honestly in the project demo; do not claim the model is already production-accurate.
