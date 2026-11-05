# Version 1 — Online: Live Kolkata + CSV Upload

## What users see

The Streamlit Community Cloud website contains exactly two pages:

1. **Live Kolkata Dashboard** — Streamlit calls FastAPI on Render. FastAPI obtains current traffic from TomTom and weather from OpenWeather, then returns the ML prediction.
2. **CSV Upload Prediction** — users upload a traffic/weather CSV. The page runs the repository's ML model locally in the Streamlit app and provides a downloadable prediction CSV. It does not call the external APIs or FastAPI.

## Streamlit Community Cloud

- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main`
- Main file: `frontend/app.py`
- Requirements file: `frontend/requirements.txt`

Set the following in Streamlit App Settings → Secrets. Replace the URL with the actual Render service URL:

```toml
BACKEND_URL = "https://YOUR-RENDER-SERVICE.onrender.com"
REQUEST_TIMEOUT_SECONDS = "90"
HEALTH_TIMEOUT_SECONDS = "90"
SEND_LOCATION_TO_BACKEND = "true"
```

Do not put TomTom or OpenWeather API keys in Streamlit Secrets.

## Render FastAPI service

**Root Directory must remain blank (repository root).** The backend imports the top-level `ml/` package and reads `data/raw/kolkata_traffic_weather.csv`.

- Build command: `pip install -r backend/requirements.txt && python backend/prepare_model.py`
- Start command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Auto Deploy: On, if reviewed merges to `main` should deploy automatically.
- Environment variables: `TOMTOM_API_KEY`, `OPENWEATHER_API_KEY`, `CITY=Kolkata`, `LATITUDE=22.5726`, `LONGITUDE=88.3639`, `REQUEST_TIMEOUT=10`.

The root `render.yaml` describes the same service for a new Render Blueprint. For an existing service, verify its Dashboard settings; adding the file does not automatically change an existing service.

## Online verification

1. Open `/health`; confirm `status=ok` and both API configured flags are true.
2. Open `/api/v1/model/status`; confirm `ready=true`.
3. Open `/api/v1/data/current`; verify current traffic and weather data.
4. Open `/docs`; test `POST /api/v1/predict` with an empty JSON object `{}`.
5. Open the Streamlit website and test both pages: Live Kolkata Dashboard and CSV Upload Prediction.

## Prediction interpretation

The model predicts a congestion class approximately 15 minutes after each input observation timestamp. It is not necessarily a forecast 15 minutes from the current clock time.
