# TrafficIQ — Kolkata Traffic Congestion Prediction System

**City:** Kolkata, India · **Prediction horizon:** 15 minutes after each observation · **ML:** Random Forest · **Frontend:** Streamlit · **Backend:** FastAPI

This five-member project uses real traffic observations collected through TomTom and weather observations from OpenWeather. It does not use physical road sensors. ML source code is written in Python `.py` files; no notebooks are required.

# The only two ways to use this project

## 1. Online — Live Kolkata + CSV Upload

The public Streamlit website has two pages:

- **Live Kolkata Dashboard:** Streamlit calls the FastAPI backend deployed on Render. FastAPI collects current traffic from TomTom and weather from OpenWeather, then runs the ML model.
- **CSV Upload Prediction:** upload a traffic/weather CSV and get predictions. This page runs the Python ML model directly and does not need the live APIs.

Online architecture:

```text
TomTom API ─────┐
                ├──> FastAPI (Render) ──> ML model ──> Live Streamlit page
OpenWeather API ┘

CSV file ─────────────────> ML model ──> CSV Streamlit page
                                  |
                                  └──> Prediction CSV download
```

### Online deployment settings

**Streamlit Community Cloud**
- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main`
- Main file: `frontend/app.py`
- Requirements: `frontend/requirements.txt`
- Secret: `BACKEND_URL = "https://YOUR-RENDER-SERVICE.onrender.com"`

**Render FastAPI**
- Root Directory: leave blank (repository root)
- Build: `pip install -r backend/requirements.txt && python backend/prepare_model.py`
- Start: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Environment variables: `TOMTOM_API_KEY`, `OPENWEATHER_API_KEY`, `CITY=Kolkata`, `LATITUDE=22.5726`, `LONGITUDE=88.3639`, `REQUEST_TIMEOUT=10`

Keep API keys only in Render Environment settings. Never commit keys to GitHub or put them in the public frontend.

## 2. Local PC — Download and Run Completely Offline

This is a separate local-only Streamlit app. It has exactly two choices:
- **Kolkata saved historical data:** predicts using the real historical CSV bundled in the repository.
- **Upload your own CSV:** predicts using a CSV file already saved on your computer.

It does not start or contact FastAPI. It does not call TomTom or OpenWeather. Offline maps have no online background tiles.

### Important first-time setup

Download/clone the repository and install Python packages while the computer has internet access. Once the repository, dataset, Python packages and model are present on the PC, disconnect the internet and run the local app. The application itself then works without internet. A fresh PC cannot download GitHub files or install missing packages while disconnected.

### Windows steps

1. Download the repository ZIP from GitHub, or clone it:
   ```powershell
   git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git
   cd traffic-congestion-prediction
   ```
2. Install Python 3.11. Open PowerShell in the project folder:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r frontend/requirements.txt
   ```
3. Prepare the ML model once (uses the bundled historical CSV; no external API):
   ```powershell
   python backend/prepare_model.py
   ```
4. Now disconnect from the internet. Start the local application:
   ```powershell
   python -m streamlit run frontend/local_app.py
   ```
5. Open the local address printed in the terminal (usually `http://localhost:8501`).

The local app opens in your browser but runs on your own PC. Keep the terminal open while using it.

### CSV format

Required, case-sensitive columns:

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional columns: `latitude`, `longitude`, `time_zone` (for example, `Asia/Kolkata`). Timestamps must include a timezone or UTC marker.

## Model and limitations

The model predicts a congestion class approximately 15 minutes after each input observation timestamp. It does not mean a prediction 15 minutes from the current clock time.

The recorded held-out evaluation reports **60.22% accuracy** and **54.81% macro F1**, while the majority-class baseline accuracy is **79.77%**. This is a prototype and currently performs below that baseline; do not describe it as a reliable production-grade or city-independent forecast. The model was trained on Kolkata data; other-city predictions are experimental.

## Project structure

- `frontend/app.py`: online website with Live and CSV pages
- `frontend/legacy_live_app.py`: online Live Kolkata dashboard page
- `frontend/csv_app.py`: shared CSV prediction interface
- `frontend/local_app.py`: local offline-only launcher (historical CSV or uploaded CSV)
- `backend/`: FastAPI service and external API integration for the online version
- `ml/`: Python data cleaning, training, prediction and evaluation code
- `data/raw/kolkata_traffic_weather.csv`: bundled historical observations
- `documentation/`: project report, presentation and setup documentation

## Public visitor counter\n\nThe live dashboard displays approximate browser-session visits using the FastAPI endpoints `POST /api/v1/visit` and `GET /api/v1/visits`. It is not a unique-person counter and does not store visitor identity or IP addresses.

For persistent GitHub-backed storage, configure these environment variables in the **Render backend service**:
- `VISITS_GITHUB_TOKEN`: a fine-grained GitHub token with Contents read/write permission for this repository.
- `VISITS_GITHUB_REPO`: `Tapas-Halder/traffic-congestion-prediction` (optional default).
- `VISITS_GITHUB_BRANCH`: `traffic-visit-data` (optional default).
- `VISITS_GITHUB_PATH`: `data/visits.json` (optional default).

The token must be stored only in Render Secrets / Environment, never committed to the repository or placed in Streamlit frontend secrets. Each new Streamlit browser session updates the small JSON counter file on the dedicated data branch. Without `VISITS_GITHUB_TOKEN`, local SQLite storage is used instead. GitHub API rate limits apply, so this is suitable for a small project/demo counter rather than high-traffic production analytics.\n\n## Team workflow

The team leader maintains `main`. Other team members work on their own branches and submit Pull Requests. The team leader reviews, tests and merges changes.
