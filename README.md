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

GitHub Actions is configured to collect all monitored Kolkata road checkpoints automatically.

Each scheduled run:
1. calls OpenWeather once for Kolkata weather;
2. calls TomTom separately for each monitored road checkpoint;
3. appends the checkpoint rows to `data/raw/kolkata_traffic_weather.csv`;
4. writes a successful-run heartbeat to `data/status/last_successful_collection_utc.txt`;
5. commits both files to `main`.

Current monitored checkpoints:
- Howrah Bridge
- Esplanade
- Park Circus
- Science City
- Chingrighata
- Sector V
- Shyambazar
- Ultadanga
- Airport / Jessore Road
- Ruby / EM Bypass
- Garia / EM Bypass
- Park Street

The schedule runs every 15 minutes using the Asia/Kolkata timezone.

### Important: scheduled workflow troubleshooting

GitHub scheduled workflows are not guaranteed to start at an exact minute. They can be delayed, especially during high-load periods.

Also check that GitHub Actions is enabled for this repository and that this workflow is present on the repository's default branch.

To test immediately:
**Actions -> Collect Kolkata traffic and weather data -> Run workflow**

After a successful run, verify:
- `data/raw/kolkata_traffic_weather.csv` has new rows;
- `data/status/last_successful_collection_utc.txt` has a new timestamp;
- the workflow run shows green/success.

If the manual run succeeds but scheduled runs never appear, the problem is the GitHub Actions scheduling/settings rather than the Python collector.

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
