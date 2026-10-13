# TrafficIQ — Kolkata Traffic Congestion Prediction System

A working student project using real TomTom traffic and OpenWeather observations, a Python Random Forest classifier for 15-minute-ahead congestion, FastAPI on Render, and a Streamlit dashboard on Streamlit Community Cloud. No physical sensors or fabricated live observations.

## Architecture

1. **Scheduled collection:** External scheduler triggers GitHub Actions event `collect-kolkata-data` (or use manual workflow dispatch). `backend/data_collector.py` queries TomTom for 12 Kolkata road checkpoints and OpenWeather for Kolkata weather, appending rows to `data/raw/kolkata_traffic_weather.csv`.
2. **Model:** `ml/clean_data.py` cleans historical data; `ml/train_model.py` trains a 15-minute-ahead Random Forest; `ml/random_forest_model.py` loads the trained artifact and predicts. Training uses actual historical observations; sufficient valid timestamp pairs and multiple classes are required.
3. **Backend:** Render runs FastAPI (`backend/app/main.py`) and loads the trained model prepared during the build. The backend owns TomTom and OpenWeather API keys.
4. **Road routing:** `GET /api/v1/route` uses TomTom Routing API for real drivable road geometry and samples up to six TomTom Traffic Flow observations to colour approximate stretches green/orange/red/grey. Road distance and ETA come from TomTom route summary; colours are estimates between sampled points, not measured continuously. Routing entitlement and quota must be enabled for the TomTom key.
5. **Frontend:** Streamlit Community Cloud runs `frontend/app.py` and calls the public Render FastAPI over HTTPS. No local ML training or API keys are needed on Streamlit.

## Live services and verification

- Render backend: https://kolkata-traffic-api.onrender.com
- Health: https://kolkata-traffic-api.onrender.com/health
- Current data: https://kolkata-traffic-api.onrender.com/api/v1/data/current?latitude=22.5726&longitude=88.3639
- Model status: https://kolkata-traffic-api.onrender.com/api/v1/model/status
- Interactive API documentation: https://kolkata-traffic-api.onrender.com/docs
- Route: `/api/v1/route?from_lat=22.585&from_lon=88.346&to_lat=22.58&to_lon=88.41` (requires TomTom Routing API access).
- Prediction: `POST /api/v1/predict` with JSON `{"latitude":22.5726,"longitude":88.3639}`.

The team reported successful Render health, live data and ML prediction (HTTP 200), and successful Streamlit deployment on 13 October 2026. This is a report of observed tests, not an uptime guarantee.

## Deploy Render FastAPI

Repository: `Tapas-Halder/traffic-congestion-prediction`; branch `main`; root directory empty.

- Build: `pip install -r backend/requirements.txt && python scripts/prepare_model.py`
- Start: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Environment secrets: `TOMTOM_API_KEY`, `OPENWEATHER_API_KEY`.

The build prints `MODEL READY` or `MODEL NOT READY`. A ready model is necessary for inference. New historical CSV commits do **not** retrain an already-running Render service automatically unless Render rebuilds and executes model preparation again.

## Deploy Streamlit

Streamlit Community Cloud → New app → repository `Tapas-Halder/traffic-congestion-prediction`, branch `main`, main file `frontend/app.py`.

Set **Streamlit Secrets**:

```toml
BACKEND_URL = "https://kolkata-traffic-api.onrender.com"
REQUEST_TIMEOUT_SECONDS = 90
```

Root `requirements.txt` installs only frontend dependencies. Backend/ML dependencies are installed on Render from `backend/requirements.txt`.

## GitHub Actions CSV collection

Workflow: `.github/workflows/collect-kolkata-data.yml`

- GitHub repository **Settings → Secrets and variables → Actions**: configure `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY`.
- External scheduler: dispatch the event `collect-kolkata-data`; check scheduler credentials and schedule separately.
- GitHub → Actions → **Collect Kolkata traffic and weather data** → **Run workflow** to test manually.
- Successful runs append new observations to `data/raw/kolkata_traffic_weather.csv` and commit **only this CSV** to `main`. Partial checkpoint failures are logged.
- Verify the latest CSV timestamps and workflow history. A successful deploy does not prove the external scheduler continues to fire.

## Local development

```bash
pip install -r backend/requirements.txt
python scripts/prepare_model.py
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```bash
pip install -r frontend/requirements.txt
# Configure BACKEND_URL to the running API or use Streamlit Secrets
streamlit run frontend/app.py
```

Offline tests: `python ml/test_model.py` and `python tests/test_integration.py`. Keep ML implementation in Python `.py` files. Generated `.joblib` artifacts are ignored by Git; Render prepares them from historical CSV.

## Team collaboration

The team leader maintains `main`. Members work in their own branches, open pull requests, and merge after review. Never commit API keys or Streamlit Secrets.

## Notes

Render free instances can sleep when idle; frontend requests may take longer after wake-up. The historical CSV is intentionally retained and must not be deleted during cleanup. Model predictions are estimates, not guaranteed traffic conditions.
