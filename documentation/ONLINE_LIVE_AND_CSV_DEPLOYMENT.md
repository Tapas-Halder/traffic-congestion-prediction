# Online deployment: Live Kolkata + CSV Prediction

## Intended behaviour

The Streamlit Community Cloud app has two sidebar pages:

1. **Live Kolkata Dashboard** — calls the FastAPI service on Render. Render owns TomTom and OpenWeather credentials and runs the ML inference.
2. **CSV Upload Prediction** — runs the repository's Python-only ML model against the uploaded CSV. It does not call TomTom, OpenWeather, or the Render backend.

## Streamlit Community Cloud

- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main`
- Main file: `frontend/app.py`
- Requirements file: `frontend/requirements.txt`

Add these values under Streamlit App Settings → Secrets (replace the URL with the actual Render service URL):

```toml
BACKEND_URL = "https://YOUR-RENDER-SERVICE.onrender.com"
REQUEST_TIMEOUT_SECONDS = "90"
HEALTH_TIMEOUT_SECONDS = "90"
SEND_LOCATION_TO_BACKEND = "true"
```

Do not put TomTom or OpenWeather keys in Streamlit Secrets.

## Render FastAPI service

**Important: leave Root Directory blank (repository root).** The backend imports the top-level `ml/` package and reads `data/raw/kolkata_traffic_weather.csv`. Setting Root Directory to `backend` can make files outside that directory unavailable to the Render build.

- Build command: `pip install -r backend/requirements.txt && python backend/prepare_model.py`
- Start command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Auto Deploy: On, so reviewed merges to `main` are deployed.
- Environment variables: `TOMTOM_API_KEY`, `OPENWEATHER_API_KEY`, `CITY=Kolkata`, `LATITUDE=22.5726`, `LONGITUDE=88.3639`, `REQUEST_TIMEOUT=10`.

The root-level `render.yaml` describes the same service for a new Render Blueprint. For an existing service, verify/update its Dashboard settings; adding the file does not guarantee existing service settings change automatically.

## Verify after deployment

1. Open `/health`: confirm `status=ok` and both *_configured flags are true.
2. Open `/api/v1/model/status`: confirm `ready=true`.
3. Open `/api/v1/data/current`: verify live TomTom and OpenWeather payloads.
4. Open `/docs`, execute `POST /api/v1/predict` with an empty JSON body `{}`.
5. In Streamlit, verify both sidebar pages. The Live page should show live source/backend errors rather than fabricated values if an upstream service fails. Upload a CSV in the second page and download the predictions.

## ML interpretation

The model predicts a congestion class approximately 15 minutes after each input observation. CSV predictions are not a forecast 15 minutes from the current wall-clock time. Model probability is not a calibrated reliability guarantee. The model is trained on Kolkata observations; other cities are experimental.
