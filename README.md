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

Automatic collection is triggered by an external scheduler (cron-job.org) through GitHub's `repository_dispatch` event.

Each collection run:
1. calls OpenWeather once for Kolkata weather;
2. calls TomTom separately for each monitored road checkpoint;
3. appends the checkpoint rows to `data/raw/kolkata_traffic_weather.csv`;
4. commits the updated CSV to `main`.

The external scheduler is configured separately from this repository. For testing, it can run every 5 minutes; after successful testing, use every 15 minutes.

### Automatic collection

The GitHub workflow supports:
- manual `workflow_dispatch` for testing;
- external `repository_dispatch` from the scheduler.

The external scheduler sends:
- POST to GitHub's repository dispatch endpoint;
- event type: `collect-kolkata-data`;
- a GitHub token with repository Contents write permission.

Keep the TomTom and OpenWeather keys only in GitHub Actions Secrets. Do not put either API key in the external scheduler.

For a manual test:
**Actions -> Collect Kolkata traffic and weather data -> Run workflow**

A successful collection adds new rows to `data/raw/kolkata_traffic_weather.csv`.

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
- Data collection automation: External scheduler + GitHub repository dispatch configured
- ML: Random Forest in progress
- Frontend: Streamlit in progress
- Integration: Pending
- Deployment: Pending

## Team

- Team Leader: Backend & API
- ML Team: Random Forest model
- Frontend Team: Streamlit dashboard + documentation
