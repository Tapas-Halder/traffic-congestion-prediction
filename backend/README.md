# FastAPI backend and API collection

The backend serves Kolkata traffic and weather data from **TomTom Traffic API** and **OpenWeather API**, and provides 15-minute-ahead congestion predictions using the project's Python Random Forest model. No physical sensors are used.

## Run locally

From the repository root (Python 3.11 recommended):

```bash
python -m pip install -r backend/requirements.txt
python scripts/prepare_model.py
uvicorn app.main:app --app-dir backend --reload
```

Set `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` in the environment or a local `.env` file; see [example](../.env.example). **Never commit credentials.**

Open `http://127.0.0.1:8000/docs` for the interactive endpoint schema.

## Main endpoints

- `GET /health` — service health and configuration indicators; does not guarantee working upstream APIs or a trained model.
- `GET /api/v1/model/status` — trained-model readiness.
- `GET /api/v1/data/current?latitude=22.5726&longitude=88.3639` — current TomTom traffic and OpenWeather readings.
- `POST /api/v1/predict` with JSON `{"latitude":22.5726,"longitude":88.3639}` — 15-minute-ahead congestion prediction, when the model is available.
- `GET /api/v1/route?from_lat=22.585&from_lon=88.346&to_lat=22.58&to_lon=88.41` — route geometry and sampled traffic conditions; see the main README for TomTom/OSRM limitations.

## Data collection

`backend/data_collector.py` collects traffic at 12 monitored Kolkata road checkpoints and current weather, appending to `data/raw/kolkata_traffic_weather.csv`. The GitHub Actions workflow `.github/workflows/collect-kolkata-data.yml` accepts manual and external dispatches, **but its collection job is intentionally paused** after more than 10,000 rows were collected. It will not collect more data until explicitly re-enabled.

## Model and deployment

`scripts/prepare_model.py` cleans the historical CSV and trains `ml/artifacts/congestion_model.joblib` if enough valid 15-minute observation pairs and class diversity exist. The artifact is generated at build/runtime and is not committed.

Render backend build command:

```bash
pip install -r backend/requirements.txt && python scripts/prepare_model.py
```

Render start command:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

For deployment details, see [main README](../README.md) and [deployment guide](../STREAMLIT_CLOUD_DEPLOYMENT.md).
