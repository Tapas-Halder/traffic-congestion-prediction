# Traffic Congestion Prediction System

Simple Kolkata-focused traffic congestion prediction system using real-world external API data.

## Technology

- Frontend: Streamlit
- Backend/API: FastAPI
- Traffic data: TomTom Traffic Flow API
- Weather data: OpenWeather API
- Machine Learning: Python + Random Forest
- Data storage: CSV
- Version control: GitHub
- Deployment target: Vercel

## Project scope

The first version focuses on Kolkata city. No physical sensors are used. Traffic and weather information comes from external APIs.

## Current project structure

```
traffic-congestion-prediction/
├── backend/
│   ├── data_collector.py
│   └── main.py
├── frontend/
│   └── app.py                 # Streamlit dashboard
├── ml/
│   ├── train_model.py         # Random Forest training
│   └── predict.py             # Prediction helper
├── data/
│   └── raw/
│       └── kolkata_traffic_weather.csv
├── docs/
├── .github/
│   └── workflows/
│       └── collect-kolkata-data.yml
├── .env.example
├── .gitignore
└── README.md
```

## Data collection

GitHub Actions automatically collects one Kolkata traffic + weather row every 15 minutes.

Schedule:
- every 15 minutes: `*/15 * * * *`

The workflow runs on the `main` branch and uses the GitHub Actions secrets:
- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`

Collected data is appended to:

`data/raw/kolkata_traffic_weather.csv`

### Important about the 15-minute schedule

GitHub Actions scheduled workflows are automatic but **not a hard real-time timer**. GitHub may delay a scheduled run by a few minutes during high load. The schedule therefore means "run about every 15 minutes", not an exact clock guarantee.

For testing, use:
**Actions -> Collect Kolkata traffic and weather data -> Run workflow**

The workflow has a manual trigger as well as the automatic schedule.



Never commit API keys.

Required GitHub Actions secrets:

- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`

Local development can use a `.env` file.

## ML

The ML team will initially use synthetic data only to develop the pipeline.

Model: Random Forest.

Target:

- Low
- Medium
- High

When enough real API data is available, the model must be retrained and evaluated with the real dataset.

No Jupyter Notebook or Colab is required. Keep the ML implementation in Python `.py` files.

## Frontend

The frontend is a Streamlit application.

The dashboard will show:
- Kolkata traffic status
- current speed
- weather
- temperature
- humidity
- rainfall
- Random Forest congestion prediction

The Streamlit frontend will later call FastAPI endpoints.

## Final data flow

TomTom + OpenWeather
        ↓
Data Collector
        ↓
CSV
        ↓
Random Forest
        ↓
FastAPI
        ↓
Streamlit
        ↓
Kolkata Traffic Dashboard

## Git workflow

Team members should work on their own branches.

Branch -> Commit -> Push -> Pull Request -> Team Leader review -> Merge

## Development status

- Backend/API: Done
- Data collection automation: Configured; scheduled collection is best-effort
- ML: Random Forest in progress
- Frontend: Streamlit in progress
- Integration: Pending
- Deployment: Pending

## Team

- Team Leader: Backend & API
- ML Team: Random Forest model
- Frontend Team: Streamlit dashboard + documentation
