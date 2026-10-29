# TrafficIQ simple two-edition guide

## Public website (Streamlit Community Cloud)
Deploy **only** `frontend/app.py` on branch `main` after the PR passes and is merged.

- **Next 15 minutes** (default): Kolkata location selector; button calls the configured FastAPI backend on Render, which owns TomTom/OpenWeather and ML prediction. Shows one simple congestion label.
- **Upload city CSV**: users worldwide can upload traffic/weather CSV and get 15-minute-ahead predictions for their *historical observations*. Coordinates plot worldwide, not Kolkata-only. CSV predictions run inside Streamlit without calling TomTom/OpenWeather or Render. The model was trained on Kolkata observations and has NOT been validated for other cities; do not claim city-generalized accuracy. Feature hour is currently derived in Kolkata timezone even for global CSV, another generalization limitation.

## Local offline edition (NOT deployed online)
Install the GitHub repository locally, open a terminal in the repo root and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/local_app.py
```

Open http://localhost:8501. Use the saved Kolkata historical CSV or upload CSV from any country. Model inference runs locally without FastAPI/Render or external API calls. OpenStreetMap background tiles need internet; marker predictions themselves do not. For completely disconnected usage, map background may be blank.

## Developer setup: local FastAPI with real public frontend
In the Streamlit Community Cloud **app secrets**, set:

```toml
BACKEND_URL = "https://YOUR-PUBLIC-HTTPS-FASTAPI-URL"
```

A browser-hosted Streamlit server cannot reach `http://localhost:8000` on a developer laptop. Expose the local FastAPI server through a secured public HTTPS tunnel for development (or use Render), then configure the HTTPS URL in Cloud Secrets. Keep TomTom/OpenWeather API keys only on the backend; never commit them. Do not expose an unauthenticated development API publicly for extended periods.

Alternatively, for a fully local developer test, run FastAPI locally and run `frontend/app.py` locally with `BACKEND_URL=http://127.0.0.1:8000`.

## CSV columns
`timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm` and optionally `latitude,longitude` for the map. Values must be actual recorded observations. Prediction time is observation time plus 15 minutes; this is **not** 15 minutes from the user's current clock.

## Validation before release
1. GitHub Actions must pass on the new branch.
2. Confirm live Kolkata button returns a genuine backend prediction.
3. Upload a valid Kolkata CSV and a valid non-Kolkata CSV with lat/lon; check map centers on the uploaded coordinates.
4. Verify local_app.py launches without Render.
5. Verify local backend is accessible through an HTTPS tunnel before connecting public Cloud frontend.
