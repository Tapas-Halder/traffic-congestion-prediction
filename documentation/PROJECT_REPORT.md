# TrafficIQ — Kolkata Traffic Congestion Prediction System

**Project report | Draft for verification | 28 October 2026**

## Abstract
TrafficIQ is a five-member project that uses TomTom traffic flow observations and OpenWeather weather observations for Kolkata. Historical records feed a Python Random Forest classifier trained to predict congestion levels approximately 15 minutes ahead. FastAPI serves predictions and traffic data; Streamlit provides a dashboard. The system uses external APIs rather than physical sensors.

## Problem and objectives
Traffic conditions change with time and weather. The project aims to collect real observations, prepare a reproducible dataset, train and evaluate a future congestion classifier, and expose its results through an accessible web application. Scope is a simplified Kolkata demonstration, not citywide traffic-signal control.

## Architecture
TomTom + OpenWeather -> CSV dataset -> cleaning and feature engineering -> Random Forest training -> saved model -> FastAPI -> Streamlit dashboard.

## Implementation
- **Data:** `backend/data_collector.py`; source CSV `data/raw/kolkata_traffic_weather.csv`. Collection is paused after more than 10,000 observations as documented in the repository.
- **ML:** `ml/clean_data.py`, `ml/train_model.py`, `ml/random_forest_model.py`, `ml/test_model.py`. Inputs include current/free-flow speed, speed ratio, traffic confidence, temperature, humidity, rain, hour, and weekday.
- **Labels:** future Low/Moderate/Heavy congestion based on future speed ratio; training pairs readings from the same location approximately 15 minutes apart (±5 minutes).
- **Evaluation design:** chronological 80/20 split, with future-target boundary protection; accuracy, macro F1, confusion matrix and majority-class baseline are printed by the training script. Actual scores are **not yet verified** in this report.
- **Backend:** `backend/app/main.py` exposes `/health`, `/api/v1/data/current`, `/api/v1/predict`, `/api/v1/predict/offline`, and `/api/v1/model/status`. `backend/app/routes.py` provides `/api/v1/route` with TomTom and conditional OSRM fallback.
- **Frontend:** `frontend/app.py` and `frontend/traffic_core.py` implement the Streamlit user interface and backend integration.

## Deployment
Backend is configured for Render; frontend is configured for Streamlit Community Cloud. The deployed services must be tested again before submission. Credentials belong in environment variables or platform secrets, never in source code.

## Testing and results
The repository contains `ml/test_model.py` and `other-files/tests/test_integration.py`. Previous project discussion reported successful public offline prediction, but no current run logs, model scores or final screenshots have been supplied for independent confirmation. Record actual test date, commit SHA, dataset row counts, accuracy, macro F1, confusion matrix, endpoint responses, and screenshots before final sign-off.

## Known limitations
- No physical sensors; observations depend on third-party API availability and quotas.
- Road routing traffic status is sampled at limited route points, not full road coverage.
- OSRM fallback does not supply live traffic-aware travel time.
- The classifier targets three congestion categories for a 15-minute horizon, not an exact future speed or guaranteed citywide forecast.
- Render free-tier cold starts may delay responses.

## Security
Rotate any API key that has been shared outside secure secret storage; configure replacement keys on Render. Do not publish credentials in screenshots, documentation, or GitHub.

## Team contributions
- Tapas Halder — Team leader, backend, API collection/integration, deployment and GitHub management.
- Soumyadeep Mandal — Streamlit frontend and visualization.
- Sumit Kumar Mandal — data cleaning and Random Forest development.
- Subhajit Podder — model training, evaluation and prediction implementation.
- Pammi Biswas — documentation.

## Evidence required before submission
1. Final training metrics and class distribution.
2. Screenshots of Streamlit dashboard, offline prediction, live prediction and map.
3. Successful Render `/health` and `/api/v1/model/status` responses.
4. Test command outputs and known-failure screenshots.
5. Final team approval, date, commit hash and faculty/organization details.

## References
- Project repository: https://github.com/Tapas-Halder/traffic-congestion-prediction
- Internal project requirements: uploaded Traffic Congestion Prediction System and coding/submission guidelines.
