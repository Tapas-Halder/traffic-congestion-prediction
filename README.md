# TrafficIQ — Kolkata Traffic Congestion Prediction System

**City focus:** Kolkata, India · **Forecast horizon:** 15 minutes · **ML:** Random Forest · **Frontend:** Streamlit

This five-member project uses real traffic observations collected through TomTom and weather observations from OpenWeather. It does not use physical road sensors. The ML pipeline and all model code are Python `.py` files; no notebook is required.

## Two separate ways to run the project

| Mode | Entry point | Needs |
|---|---|---|
| Public online demo | `frontend/app.py` | CSV upload + trained model; no FastAPI, Render, TomTom or OpenWeather calls |
| Local laptop | `frontend/local_app.py` | Saved Kolkata historical CSV or uploaded CSV; no website |
| Optional local live-data developer mode | `backend/app/main.py` + `frontend/legacy_live_app.py` | Internet, local FastAPI, TomTom/OpenWeather keys |

**Public website is CSV-upload only.** A CSV must contain observed traffic/weather data. The model predicts the congestion class 15 minutes after each row's timestamp; it does not claim to predict 15 minutes from the current clock time.

## Public Streamlit Community Cloud deployment

- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main` (after merging the CSV-only deployment PR)
- Main file: `frontend/app.py`
- Dependencies: `frontend/requirements.txt`
- No `BACKEND_URL`, Render service, or external API secrets are required for this public CSV workflow.

The public app prepares the trusted Random Forest from the repository's real historical dataset when the model artifact is not already present. First startup can take longer because training runs on the Streamlit instance.

## Run locally on Windows

Install Git and Python 3.11. Open PowerShell:

```powershell
git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git
cd traffic-congestion-prediction
git switch main
git pull origin main
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/local_app.py
```

Select **Kolkata saved data** to predict from the historical dataset, or **Upload city CSV** to upload a CSV. These modes do not call APIs or a website. Initial setup/package installation needs internet; after dependencies and data are present, inference can run offline. Map background tiles need internet.

## CSV columns

Required, case-sensitive columns:

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional: `latitude`, `longitude`, `time_zone` (e.g. `Asia/Kolkata`). Timestamps should be UTC ISO 8601. The Kolkata-trained model has not been validated for other cities; predictions for other cities are experimental.

## Optional local FastAPI/API collection

The FastAPI service remains in `backend/` for local development and future use. It is not part of the public CSV-only website. Keep `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` in a local `.env` file or private deployment secrets; never commit keys.

## Project structure

- `frontend/app.py`: public CSV-only Streamlit entry point
- `frontend/csv_app.py`: CSV validation, prediction, charts/maps and downloads
- `frontend/local_app.py`: laptop-only historical/CSV/full-dashboard selector
- `backend/`: optional FastAPI and external API integration
- `ml/`: data cleaning, training, inference and evaluation scripts (`.py`)
- `data/raw/kolkata_traffic_weather.csv`: real historical observations
- `documentation/`: reports, evaluation and deployment guides
- `other-files/tests/`: tests

## Model evaluation disclosure

The repository's recorded held-out evaluation reports **60.22% accuracy** and **54.81% macro F1**, while the majority-class baseline accuracy is **79.77%**. The model is a prototype and currently performs below that baseline. Do not describe it as a reliable production-grade or city-agnostic forecast. Improve the dataset, features and evaluation before making such claims.

## Team workflow

The team leader owns `main`. The other four members work on separate feature branches and open Pull Requests. The team leader reviews, tests and merges PRs.

## Basic checks

```powershell
python -m compileall -q frontend backend ml
python -m unittest discover -s other-files/tests -p "test_csv_inference.py" -v
python backend/prepare_model.py
python ml/test_model.py
```

A passing unit test does not by itself prove that the Streamlit deployment or external APIs are available.
