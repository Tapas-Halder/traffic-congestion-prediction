# TrafficIQ — Kolkata Traffic Congestion Prediction System

A five-member student project using real TomTom traffic and OpenWeather data, a Python Random Forest model for 15-minute-ahead congestion, FastAPI, and Streamlit. No physical sensors or fabricated live data.

## Repository structure

```text
traffic-congestion-prediction/
├── frontend/              # Streamlit dashboard and requirements
├── backend/               # FastAPI, API collector, model preparation
├── ml/                    # ML entry point, src/, Random Forest, analysis and outputs
├── data/                  # Real Kolkata historical CSV
├── other-files/           # Integration tests, supplementary documentation
└── README.md
```

Original files and the former GitHub Actions workflows remain safe in the [Backup branch](https://github.com/Tapas-Halder/traffic-congestion-prediction/tree/Backup). Data collection is intentionally paused after 10,000+ real observations.

## How it works

1. `backend/data_collector.py` collects TomTom traffic and OpenWeather observations at Kolkata checkpoints, saved in `data/raw/kolkata_traffic_weather.csv`.
2. `ml/clean_data.py` cleans the real observations. `ml/train_model.py` trains a Random Forest using 15-minute-ahead labels.
3. `ml/random_forest_model.py` loads the trained model for FastAPI predictions.
4. `backend/app/main.py` provides health, current readings, model status and prediction APIs. `backend/app/routes.py` provides routing with TomTom and a limited OSRM fallback.
5. `frontend/app.py` shows the traffic, weather, map, routing and model results through FastAPI.

## Run locally

Python 3.11 recommended. Configure `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` as environment variables (see `backend/.env.example`). Never commit actual keys.

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
python backend/prepare_model.py
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```bash
python -m pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Frontend defaults to `http://127.0.0.1:8000`. Set `BACKEND_URL` to the deployed HTTPS backend in Streamlit Secrets.

## ML folder structure and usage

The [ML README](ml/README.md) explains `ml/main.py`, `ml/config.py`, `ml/data/`, `ml/src/`, `ml/requirements.txt` and `ml/outputs/`. The actual dataset remains under root `data/raw/` to avoid duplicate CSV files. Run `python -m ml.main all` from the repository root to clean and train.

## Offline tests and ML evaluation

```bash
python ml/test_model.py
python other-files/tests/test_integration.py
python backend/prepare_model.py
```

Verify `/health`, `/api/v1/model/status`, `/api/v1/data/current` and `POST /api/v1/predict`. Offline tests use mocks and do not prove that live API keys or deployment work.

## Deployment

**Render backend:** repository root, branch `main`. Build:

```bash
pip install -r backend/requirements.txt && python backend/prepare_model.py
```

Start:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

Set Render secrets `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY`. Backend example: https://kolkata-traffic-api.onrender.com

**Streamlit Community Cloud:** repository `Tapas-Halder/traffic-congestion-prediction`, branch `main`, entrypoint `frontend/app.py`, dependencies `frontend/requirements.txt`. Configure Streamlit Secrets:

```toml
BACKEND_URL = "https://kolkata-traffic-api.onrender.com"
REQUEST_TIMEOUT_SECONDS = 60
HEALTH_TIMEOUT_SECONDS = 60
```

**TomTom 403:** The frontend can now display available OpenWeather data even when TomTom rejects traffic requests. A 403 cannot be fixed by changing the timeout: rotate any exposed TomTom key and check Traffic Flow permissions/quota. API credentials are never included in returned error URLs. The old GitHub Actions CI and collector workflows are only on `Backup`. Historical CSV is retained; no automated collection runs from this simplified `main`.

## Team Members and Roles

This project is developed by a five-member team:

| Team member | Role | Responsibilities |
| --- | --- | --- |
| **Tapas Halder** | **Team Leader, Backend Developer & API Data Collection and Integration** | Team coordination, FastAPI backend development, TomTom Traffic API and OpenWeather API data collection, API integration, GitHub repository management, system integration and deployment. |
| **Soumyadeep Mandal** | **Frontend Developer** | Streamlit frontend development, dashboard user interface, traffic visualization and frontend-to-backend connectivity. |
| **Sumit Kumar Mandal** | **Machine Learning Developer — Part 1** | Traffic dataset preprocessing and cleaning; Random Forest model development. |
| **Subhajit Podder** | **Machine Learning Developer — Part 2** | Machine learning model training and evaluation; traffic congestion prediction implementation. |
| **Pammi Biswas** | **Documentation** | Project documentation. |


## Backend timeout and workflow troubleshooting

Render free instances can take time to wake after inactivity. The Streamlit health check previously timed out after 3 seconds; it now waits at least 60 seconds, and live requests also wait at least 60 seconds. If the error persists, confirm the Render service is running and deployed from `main`, verify its build/start commands above, and inspect its logs. The `/health` endpoint only confirms FastAPI responded; `/api/v1/data/current` needs valid TomTom/OpenWeather keys, and `/api/v1/model/status` checks ML readiness.

**Important:** To keep exactly five top-level folders and a README, the GitHub Actions workflows remain archived in `Backup`. GitHub Actions requires `.github/workflows/` at the repository root, so automated CI cannot run on this simplified `main` layout unless that additional root folder is allowed. Offline test scripts are retained under `ml/` and `other-files/tests/`.

## Submission checklist

- [x] Five folders (`frontend/`, `backend/`, `ml/`, `data/`, `other-files/`) and `README.md` at the root.
- [x] Real dataset, ML source, backend, frontend and Backup preserved.
- [ ] Run offline tests and train the model on submitted data.
- [ ] Update Render build command, redeploy and check model status.
- [ ] Verify Streamlit integration and capture final screenshots and metrics.
