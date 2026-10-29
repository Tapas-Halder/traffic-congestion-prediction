# TrafficIQ — Traffic Congestion Prediction System

**Default city:** Kolkata, India · **Forecast target:** congestion class 15 minutes after an observation · **Repository:** https://github.com/Tapas-Halder/traffic-congestion-prediction

TrafficIQ is a five-member Python project using **real TomTom traffic data**, **OpenWeather observations**, historical CSV, a **Random Forest** classifier, **FastAPI** and **Streamlit**. There are **no physical sensors**. The original Kolkata dashboard keeps Overview, Roads, Map, Route and Pipeline.

> **Accuracy disclosure:** The committed evaluation reports **60.22% accuracy** and **54.81% macro F1**, compared with **79.77% majority-class baseline accuracy**. This is a working prototype, not a verified high-accuracy or production-ready forecasting system. The model was trained on Kolkata data; other-city CSV results are experimental.

## 1. Choose the correct application

| Who | Entrypoint | What it does |
|---|---|---|
| Public online user | `frontend/app.py` | Kolkata dashboard by default, plus worldwide CSV upload |
| Local PC user | `frontend/local_app.py` | Saved Kolkata historical prediction, CSV upload, or full dashboard |
| Developer | `frontend/app.py` with `BACKEND_URL` override | Same frontend code with a locally running FastAPI backend |

**Public website** uses Streamlit Community Cloud + FastAPI on Render. Only **Traffic dashboard** and **Predict from CSV** are presented to public users. **Local-only features are not deployed as a separate public page.**

## 2. How the pipeline works

```text
TomTom traffic + OpenWeather observations (no installed physical sensors)
   -> Real historical traffic/weather CSV
   -> Data cleaning + feature engineering
   -> Random Forest classifier (.py modules)
   -> Low / Moderate / Heavy (15-minute future target)
   -> FastAPI backend and/or local CSV inference
   -> Streamlit dashboard, Kolkata route/map, global CSV point map
```

The user-provided reference pipeline describes physical sensors; our project intentionally substitutes external real-world APIs. The full project remains modular: `frontend/`, `backend/`, `ml/`, `data/`, `documentation/`, `other-files/`.

## 3. Installation on Windows — local offline use

Install **Git** and **Python 3.11**. Open PowerShell in the cloned repository folder:

```powershell
git switch main
git pull origin main
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/local_app.py
```

Open `http://localhost:8501`. Choose **Kolkata saved data** or **Upload city CSV**. These two features use the Python ML model directly and **do not need TomTom/OpenWeather/FastAPI/Render calls**. Initial package installation needs internet. If no model artifact exists, preparation may train it from the repository historical CSV.

### CSV format — Kolkata or other cities

Required columns:

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional columns: `latitude`, `longitude`, `time_zone` (IANA timezone, e.g. `Asia/Kolkata` or `Europe/London`). The model uses the observation's local hour and weekday; missing `time_zone` defaults to Kolkata time. Maximum upload: 25,000 rows. Map markers use uploaded coordinates worldwide; the OpenStreetMap tile background may not load without internet.

**CSV is not live API collection.** Upload real observed traffic/weather fields. Each predicted class refers to **15 minutes after that CSV row's timestamp**, not necessarily 15 minutes from now. A point marker is not a complete predicted road route. Global CSV input support **does not establish model accuracy in other cities**.

## 4. Developer — local FastAPI + same frontend code

In one terminal from the repository root:

```powershell
python -m pip install -r backend/requirements.txt
python backend/prepare_model.py
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

In a second terminal:

```powershell
$env:BACKEND_URL="http://127.0.0.1:8000"
python -m streamlit run frontend/app.py
```

The local API health endpoint is `http://127.0.0.1:8000/health`. **A Streamlit Community Cloud site cannot connect to your private `localhost`**. For live APIs, configure `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` securely in the backend environment. Never commit keys.

## 5. Public online deployment

**Render FastAPI**
- Install/build: `pip install -r backend/requirements.txt && python backend/prepare_model.py`
- Start: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Add backend environment secrets `TOMTOM_API_KEY`, `OPENWEATHER_API_KEY`.
- Example deployed backend: `https://kolkata-traffic-api.onrender.com`

**Streamlit Community Cloud**
- Repository: `Tapas-Halder/traffic-congestion-prediction`
- Branch: `main`
- Main file: `frontend/app.py` (**not** `frontend/local_app.py`)
- Python 3.11; frontend dependencies from `frontend/requirements.txt`.
- Streamlit Secrets:

```toml
BACKEND_URL = "https://kolkata-traffic-api.onrender.com"
REQUEST_TIMEOUT_SECONDS = 90
HEALTH_TIMEOUT_SECONDS = 90
```

Live data availability depends on Render uptime and external API quotas/permissions. Historical CSV inference can operate without backend API requests.

## 6. Code structure and developer workflow

| File/folder | Purpose |
|---|---|
| `frontend/app.py` | Public Streamlit launcher |
| `frontend/local_app.py` | Private/local Streamlit launcher |
| `frontend/legacy_live_app.py` | Original Kolkata dashboard, route and maps |
| `frontend/csv_app.py` | CSV upload, predictions and global point map |
| `frontend/traffic_core.py` | Shared API parsing/traffic utilities |
| `backend/app/` | FastAPI service, live data and routing |
| `backend/prepare_model.py` | Historical model preparation |
| `ml/clean_data.py`, `ml/train_model.py`, `ml/csv_inference.py` | ML cleaning, training and CSV inference |
| `data/raw/kolkata_traffic_weather.csv` | Collected real observations |
| `documentation/ML_EVALUATION_RESULTS.json` | Committed evaluation metrics |
| `other-files/tests/` | Tests |

Team members work on feature branches and open PRs to the leader's repository; **Tapas Halder** reviews and merges.

## 7. Tests and quality checks

```powershell
python -m compileall -q frontend backend ml
python -m unittest discover -s other-files/tests -p "test_csv_inference.py" -v
python backend/prepare_model.py
python ml/test_model.py
```

Verify the original dashboard, Render `/health`, current-data and prediction endpoints, route map, local historical CSV, worldwide CSV upload and downloadable results. A green unit test alone does **not** prove the live APIs or all deployment features work. Keep a screenshot/test log and the final Git commit SHA.

## 8. Coding Standards & Submission Guidelines review

The team-provided guidelines **prohibit Jupyter/Colab notebooks, hard-coded configuration and monolithic scripts**; they require **Python .py source, modular functions, readable code, documentation and graceful error handling**.

| Requirement | Review |
|---|---|
| Python-only ML, no notebooks in ML pipeline | **Aligned** in inspected ML entrypoints |
| Real data rather than fabricated sensor values | **Aligned** with external API architecture |
| Modular project folders and functions | **Substantially aligned** |
| Configuration and secrets | **Partially aligned** — default backend URL and landmark coordinates remain in code; configuration cleanup is advisable |
| No monolithic files | **Needs improvement** — `frontend/legacy_live_app.py` is approximately 40 KB and should be refactored into smaller components |
| Error handling, tests, documentation | **Partially aligned** — checks exist, but broader integration and release verification remain necessary |
| Production-ready / go-live capable | **Not demonstrated** — model underperforms baseline and security/load/monitoring/reliability review is incomplete |

The provided `src/` layout is **recommended**, not a strict directory naming mandate. Existing separated `ml/`, `backend/` and `frontend/` modules are a reasonable modular alternative. **Do not claim full compliance until outstanding items are addressed.**

## 9. Project team

| Member | Role |
|---|---|
| Tapas Halder | Team Leader; Backend, APIs, GitHub integration, deployment |
| Soumyadeep Mandal | Streamlit frontend |
| Sumit Kumar Mandal | ML preprocessing and feature preparation |
| Subhajit Podder | ML training and evaluation |
| Pammi Biswas | Documentation |

## 10. Submission deliverables

Submit source code, `README.md`, historical dataset (subject to licensing), evaluation record, test evidence/screenshots, and Word documents:
- `documentation/TrafficIQ_Final_Project_Report.docx`
- `documentation/TrafficIQ_Technical_Documentation.docx`

The Word files must be added to the repository's `documentation/` folder before final submission. See `documentation/SIMPLE_UI_GLOBAL_AND_LOCAL.md` for detailed workflow notes. Never include actual API keys in the submission.

## 11. Source basis

This README is grounded in the team's supplied *Traffic Congestion Prediction System* reference, supplied *Coding Standards & Project Submission Guidelines*, and repository source/evaluation files. Reported manual test passes are team observations, not independent production certification.
