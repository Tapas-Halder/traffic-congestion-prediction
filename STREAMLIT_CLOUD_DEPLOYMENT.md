# Streamlit Community Cloud + FastAPI deployment (Kolkata)

## Architecture

Streamlit Community Cloud hosts only the dashboard. **It does not run the FastAPI backend**. Host FastAPI on a separate Python ASGI service with a public HTTPS URL. That backend fetches TomTom and OpenWeather data and loads the trained Python Random Forest artifact. The frontend calls FastAPI using BACKEND_URL. Vercel is not required.

## Step 1: Prepare ML and backend

From repository root, use Python 3.11 and run:

```bash
python -m pip install -r backend/requirements.txt
python ml/clean_data.py
python ml/train_model.py
python ml/test_model.py
```

The model artifact must exist at `ml/artifacts/congestion_model.joblib` in the backend's runtime environment. If insufficient real data or class diversity prevents training, keep collecting real observations and do not claim predictions work. Never put API keys into the repository.

Deploy the **repository root** as the backend source (not the `backend/` directory alone) so `ml/` is included. Install dependencies from `backend/requirements.txt`. Start command from repo root:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}
```

Set backend environment variables: TOMTOM_API_KEY, OPENWEATHER_API_KEY (and optionally CITY, LATITUDE, LONGITUDE). Verify `https://YOUR-BACKEND-HOST/health` and test live `/api/v1/data/current` and `/api/v1/predict` with a real model artifact.

## Step 2: Streamlit Community Cloud

1. Open https://share.streamlit.io/ and choose **Create app** / **Deploy a public app from GitHub**.
2. Repository: `Tapas-Halder/traffic-congestion-prediction`; branch: `main`; main file path: `frontend/app.py`.
3. Python version: 3.11 if selectable. The root `requirements.txt` includes frontend dependencies; the root `.streamlit/config.toml` supplies the theme.
4. In **Advanced settings / Secrets**, add:

```toml
BACKEND_URL = "https://YOUR-BACKEND-HOST"
REQUEST_TIMEOUT_SECONDS = 20
SEND_LOCATION_TO_BACKEND = true
```

5. Deploy. Do not set BACKEND_URL to localhost, 127.0.0.1, or a private LAN IP: these refer to the Streamlit server, not your backend.
6. Test health, current traffic, weather, and 15-minute model prediction for a Kolkata location. If backend hosting sleeps, first request may take longer.

## Data freshness caveat

The frontend historical chart reads the CSV committed in this GitHub repository. Community Cloud does not automatically fetch the latest GitHub commits into an already-running process. Redeploy/reboot after new CSV commits, or later expose a history endpoint from FastAPI. The live traffic/weather/prediction endpoints remain dynamic.

## Verification

GitHub CI tests are **offline**, using mocked API responses and model output. They cannot establish that live API credentials, hosting, the trained model, or deployment work. Verify those separately before calling the project production-ready.
