# TrafficIQ simple UI — deployment roles

## Public online website (Streamlit Community Cloud)
Entrypoint: `frontend/app.py`. Only two choices:
- **Traffic dashboard** (default Kolkata): existing Overview, Roads, Map, Route, Pipeline. FastAPI hosted on Render. TomTom/OpenWeather access stays on the backend. Default dashboard data source is Live. It may show unavailable when APIs fail.
- **Predict from CSV**: any city if the CSV has the required columns; use `latitude`, `longitude` for global markers and optional `time_zone` (IANA, e.g. `Asia/Kolkata`, `Europe/London`) for local time features. Without `time_zone`, Kolkata timezone is assumed. This mode does **not** call external traffic/weather APIs; input must already contain observed traffic and weather data. Internet is only needed to load OpenStreetMap background tiles; without internet the ML predictions still run but background map tiles may not load.

**Important**: The existing Random Forest was trained on Kolkata. It has NOT been validated for other cities. The map displays predicted point markers, not traffic conditions for an entire route. No worldwide live-data coverage is claimed.

## Local PC (private installation, not a website feature)
Entrypoint: `frontend/local_app.py`.

```powershell
git switch main
git pull origin main
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/local_app.py
```

Use **Kolkata saved data** for offline model prediction, **Upload city CSV** for offline predictions from uploaded observations, or **Full dashboard** with an available backend. The local launcher is a separate Python file, so Cloud users do not see local-only controls.

## Developer: local FastAPI with public frontend code
Set `BACKEND_URL=http://127.0.0.1:8000` in the developer PC environment, start the backend, then run `python -m streamlit run frontend/app.py` on the developer PC. This is the same frontend *code* as the online site, connected to a local backend. **The already deployed Streamlit Community Cloud website cannot access a developer's localhost backend**. To test from the public cloud deployment, a secure publicly reachable backend URL is required; do not expose development secrets.

## Interpretation
Show only **Low / Moderate / Heavy** as the main prediction label. CSV prediction is 15 minutes after **each row's timestamp**, not 15 minutes from now. Model accuracy on the Kolkata held-out evaluation was ~60.2%, below its majority baseline; do not present it as a reliable city-agnostic forecast.
