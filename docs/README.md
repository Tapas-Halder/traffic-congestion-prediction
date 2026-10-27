# Project documentation

**Project:** TrafficIQ — Traffic Congestion Prediction System (Kolkata)

This folder is the documentation index for the submission. The project uses real TomTom Traffic and OpenWeather API observations, a Python Random Forest classifier, a FastAPI backend, and a Streamlit dashboard. There are no physical sensors.

## Read in this order

1. [Project overview, architecture, team and quick start](../README.md)
2. [Data source and historical dataset](../data/README.md)
3. [Backend API and configuration](../backend/README.md)
4. [Machine learning and end-to-end integration](../INTEGRATION.md)
5. [Streamlit dashboard](../frontend/README.md)
6. [Streamlit Cloud and FastAPI deployment](../STREAMLIT_CLOUD_DEPLOYMENT.md)

## Team members

| Name | Responsibility |
| --- | --- |
| Tapas Halder | Team leader; FastAPI backend; TomTom and OpenWeather API data collection and integration; deployment |
| Soumyadeep Mandal | Streamlit frontend and visualization |
| Sumit Kumar Mandal | ML part 1: preprocessing and Random Forest model development |
| Subhajit Podder | ML part 2: model training, evaluation and congestion prediction |
| Pammi Biswas | Documentation |

## Submission verification

Run from the repository root after installing dependencies:

```bash
python ml/test_model.py
python tests/test_integration.py
python scripts/prepare_model.py
```

These commands check local code and model readiness. Live TomTom/OpenWeather access, Render, and Streamlit Community Cloud must be checked separately. Do not include real API keys in reports or screenshots.

**Dataset:** `data/raw/kolkata_traffic_weather.csv` is intentionally retained for reproducibility. The collection workflow is currently paused after gathering over 10,000 rows; it is not an active automatic feed.
