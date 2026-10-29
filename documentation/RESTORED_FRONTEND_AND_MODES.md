# Restored original dashboard + separate CSV features

The original Streamlit UI has NOT been replaced. `frontend/app.py` is a small launcher with three modes:

1. **Original dashboard (FastAPI + Render)**: runs the preserved original `frontend/legacy_live_app.py` with its Overview, Roads, Map, Route, Pipeline, location selector, and original live/offline switch. Default backend URL: `https://kolkata-traffic-api.onrender.com`. Override `BACKEND_URL` in Streamlit secrets or environment for another backend. This mode needs a reachable FastAPI server and the external APIs for live requests.
2. **Historical offline (local ML)**: uses the repository's existing `data/raw/kolkata_traffic_weather.csv` and existing Random Forest directly; no FastAPI/Render/external API calls. Predictions refer to 15 minutes after each historical observation.
3. **CSV upload (local ML, no API)**: uploads a CSV and runs the same model directly, with table, checkpoint map and CSV download.

## Local PC (Windows PowerShell)

Open the cloned repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/app.py
```

Choose **Historical offline** or **CSV upload** to work without Render. The first run may train the model from the repository historical CSV if no saved artifact is present. Do not disconnect while installing dependencies or training.

To use **Original dashboard** on your own local FastAPI server, start FastAPI in another terminal using the existing backend README, then set `BACKEND_URL=http://127.0.0.1:8000` before starting Streamlit. Without this override, Original dashboard uses Render even on a local PC.

## Streamlit Community Cloud

Use repository `Tapas-Halder/traffic-congestion-prediction`, branch `main` after the reviewed PR is merged, entrypoint `frontend/app.py`, Python 3.11. Configure `BACKEND_URL = "https://kolkata-traffic-api.onrender.com"` in app Secrets if you need to override the default. The Original dashboard needs Render and the backend's TomTom/OpenWeather credentials for live calls. The two CSV modes do not.

**Important:** Offline CSV marker map and the five saved landmark selectors do not calculate road routes or real-time travel times. The original route feature uses the backend, with its own routing service and live samples.

Do not merge before checking both original dashboard and new CSV modes; a passing CSV CI test alone does not verify the entire legacy dashboard. API keys must remain in Render secrets, never in GitHub.
