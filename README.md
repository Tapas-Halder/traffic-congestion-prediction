# Traffic Congestion Prediction System — Kolkata

A Python project using TomTom traffic and OpenWeather weather observations for Kolkata, a Random Forest classifier, a FastAPI interface, and a Streamlit dashboard. No physical sensors.

## Deployment architecture

- **Frontend:** Streamlit Community Cloud, entry point `frontend/app.py`.
- **Backend:** FastAPI requires a separate running Python service if the frontend continues to call HTTP endpoints. Streamlit Community Cloud does **not** host a separate persistent FastAPI server automatically.
- **ML:** Python `.py` scripts; model training and inference must be wired into the deployed backend or into Streamlit itself.
- **Data collection:** GitHub Actions triggered manually or by external `repository_dispatch` scheduler; CSV at `data/raw/kolkata_traffic_weather.csv`.

## Important: integration is not yet verified

The current Streamlit frontend calls:
- `GET /health`
- `GET /api/v1/data/current` with latitude and longitude
- `POST /api/v1/predict` with location, latitude and longitude

Set `BACKEND_URL` to a **publicly reachable HTTPS FastAPI service** in Streamlit Community Cloud secrets. The default `http://127.0.0.1:8000` works only when FastAPI is running in the same local environment; it is not a hosted backend.

The following expected paths were not found in the reviewed `main` branch and require implementation or confirmation of equivalent files:
- `backend/main.py`
- `ml/predict.py`
- `data/processed/kolkata_traffic_weather_clean.csv`
- `ml/artifacts/congestion_model.joblib`

The training script `ml/train_model.py` defaults to the processed CSV path and saves a `.joblib` artifact. `.gitignore` currently excludes `.joblib` files. Establish a deliberate artifact delivery method (build-time training, release artifact, or controlled exception) before deployment.

## Setup and testing

1. Configure `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` as GitHub Actions secrets; never commit keys.
2. In GitHub Actions run **Collect Kolkata traffic and weather data** manually and check that the raw CSV gains rows.
3. Prepare a cleaned CSV from the raw observations; validate columns and timestamps.
4. Train with `python ml/train_model.py --data data/processed/kolkata_traffic_weather_clean.csv --model ml/artifacts/congestion_model.joblib`.
5. Implement and locally test the FastAPI endpoints above, including real inference.
6. Run `pip install -r frontend/requirements.txt` and `streamlit run frontend/app.py` from the repository root; set `BACKEND_URL` to the running API.
7. Deploy the API on a suitable Python host and configure its public HTTPS URL in Streamlit Community Cloud secrets.
8. Deploy Streamlit with repository `Tapas-Halder/traffic-congestion-prediction`, branch `main`, entry point `frontend/app.py`; test every road, prediction, and error state.

## Repository dependencies

Root `requirements.txt` currently references `frontend/requirements.txt`. A separately deployed FastAPI service needs its own dependency installation including FastAPI, Uvicorn, scikit-learn, pandas, joblib and requests, with compatible pinned versions.

## Team workflow

Use feature branches and pull requests: branch → commit → push → PR → review → merge to `main`.

## Status

Data collection, training and frontend source files exist. Complete end-to-end integration, model availability, public API deployment and production dashboard operation **have not yet been verified**.
