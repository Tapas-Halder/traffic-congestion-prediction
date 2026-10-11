# Kolkata Traffic Congestion Prediction System

Streamlit Community Cloud deployable traffic and weather dashboard for Kolkata, using real TomTom and OpenWeather API data, GitHub Actions collection, and Python Random Forest prediction.

## Streamlit Community Cloud (recommended free setup)

1. Open https://share.streamlit.io and select **Create app** → **Deploy a public app from GitHub**.
2. Repository: `Tapas-Halder/traffic-congestion-prediction`; branch: `main`; entry point: `frontend/app.py`.
3. Set **App settings → Secrets** with `TOMTOM_API_KEY = "..."` and `OPENWEATHER_API_KEY = "..."`. Rotate any keys previously shared in documents or chats. **Do not set BACKEND_URL** for the recommended in-process mode.
4. The root `requirements.txt` installs Streamlit and ML/backend dependencies. The app imports the backend Python services directly: no separately hosted FastAPI server is needed.
5. At first startup the app cleans `data/raw/kolkata_traffic_weather.csv` and attempts to train the 15-minute Random Forest model locally if no model artifact exists. Insufficient valid 15-minute observation pairs will show **Model unavailable**; it does not invent predictions.
6. Click **Refresh data** and verify live traffic and weather for each Kolkata checkpoint.

## Alternative: FastAPI service

Run `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000` from repository root after installing `backend/requirements.txt`. Deploy it to an external Python hosting service and set Streamlit secret `BACKEND_URL = "https://your-api-host"`. That host must also have a trained model at `ml/artifacts/congestion_model.joblib`.

## Data and ML

GitHub Actions **Collect Kolkata traffic and weather data** calls TomTom and OpenWeather and appends observations to `data/raw/kolkata_traffic_weather.csv`. Configure the same API keys as **GitHub Actions repository secrets**. The external scheduler triggers the `collect-kolkata-data` repository_dispatch event; monitor the workflow history.

Manual local training:

```bash
python ml/clean_data.py
python ml/train_model.py
python ml/test_model.py
python tests/test_integration.py
streamlit run frontend/app.py
```

Model training requires sufficient real time-separated observations and multiple congestion classes. Do not substitute synthetic results as live predictions. All ML source code is Python `.py` files; the generated model artifact is a local `.joblib` file.

## Source modules

- `backend/data_collector.py`: scheduled API collection to CSV
- `backend/app/main.py`: optional FastAPI HTTP endpoints
- `backend/app/services/`: TomTom, weather, feature preparation, inference adapter
- `ml/clean_data.py`, `ml/train_model.py`, `ml/random_forest_model.py`: ML pipeline
- `frontend/app.py`, `frontend/traffic_core.py`, `frontend/local_backend.py`: Streamlit dashboard and in-process API adapter
- `scripts/prepare_model.py`: Streamlit startup training from historical observations

## Team workflow

Work in feature branches; open pull requests for team-leader review and merge to `main` after tests.

## Validation status

Code paths are integrated for the in-process deployment, but a successful real API request, complete model training, and a working Streamlit Cloud deployment must still be verified using actual credentials and deployment logs.
