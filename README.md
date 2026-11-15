# 🚦 TrafficIQ — Kolkata Traffic Congestion Prediction System

A Python machine-learning project that predicts road congestion in **Kolkata, India** using real-world traffic and weather observations from **TomTom Traffic API** and **OpenWeather API**. This project does **not** use physical roadside sensors.

## Quick links

- **Download the complete project:** [Download ZIP](https://github.com/Tapas-Halder/traffic-congestion-prediction/archive/refs/heads/main.zip)
- **Clone with Git:** `git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git`
- **Online application:** [Streamlit Community Cloud](https://share.streamlit.io/) (deploy from this repository)
- **Backend deployment:** Render (see [render.yaml](render.yaml))
- **Frontend instructions:** [frontend/README.md](frontend/README.md)
- **Backend instructions:** [backend/README.md](backend/README.md)
- **ML instructions:** [ml/README.md](ml/README.md)

## Project overview

| Item | Technology / choice |
|---|---|
| Initial study area | Kolkata, West Bengal, India |
| Traffic data | TomTom Traffic API |
| Weather data | OpenWeather API |
| Physical sensors | Not used |
| ML model | Random Forest classifier |
| Backend | FastAPI |
| Frontend | Streamlit |
| Online frontend hosting | Streamlit Community Cloud |
| Backend hosting | Render |
| ML code | Python `.py` files |

### How it works

1. TomTom provides traffic observations and OpenWeather provides weather information.
2. FastAPI receives the external data, prepares model inputs and calls the trained ML model.
3. The Random Forest model predicts the traffic congestion level.
4. Streamlit displays the current traffic information and prediction.
5. The CSV page can also predict congestion from a user-uploaded CSV file.

**Data note:** API observations are real-world provider data. They are not readings from physical sensors installed by this project. Live results depend on API coverage, credentials, network access and provider limits.

## Main features

- Live Kolkata traffic and weather dashboard (requires the online backend and valid API credentials).
- Machine-learning congestion predictions.
- CSV upload prediction and downloadable result.
- Local offline mode using the historical dataset and model files stored on the computer.
- Approximate visitor counter when its backend GitHub storage is configured.

## Project architecture

```text
ONLINE MODE
TomTom Traffic API ─────┐
                        ├──> FastAPI backend ──> Random Forest model
OpenWeather API ────────┘              │
                                       v
                              Streamlit dashboard

CSV upload ──> validation/preprocessing ──> ML model ──> prediction CSV

LOCAL OFFLINE MODE
Saved historical CSV / user CSV ──> Local Streamlit app ──> ML model
```

## 1. Download the repository

Choose either method.

### Option A — Download ZIP (easiest for beginners)

1. Open the [TrafficIQ GitHub repository](https://github.com/Tapas-Halder/traffic-congestion-prediction).
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. After downloading, right-click the ZIP file and choose **Extract All** (Windows).
5. Open the extracted `traffic-congestion-prediction-main` folder.

### Option B — Clone using Git

Install Git first, then open Terminal / Command Prompt and run:

```bash
git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git
cd traffic-congestion-prediction
```

## 2. Install Python and project requirements

Use **Python 3.11** (recommended for this repository). During the first setup, the computer needs internet access to download Python packages. After installation, the local CSV prediction workflow can run without internet, provided the required data and model files are present or can be generated.

Open a terminal inside the repository's main folder.

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The root `requirements.txt` installs the dependencies used by the frontend, backend and ML workflow. Component-specific files are also provided: `frontend/requirements.txt`, `backend/requirements.txt`, and `ml/requirements.txt`.

## 3. Run locally — Offline mode (no live API)

This is the local mode for a computer without a running FastAPI server. It uses the saved historical Kolkata CSV and/or a CSV uploaded by the user. It does not call TomTom, OpenWeather or the live backend.

From the **repository root**, with the virtual environment activated:

```bash
streamlit run frontend/local_app.py
```

Then:

1. Streamlit will show a local address, normally `http://localhost:8501`.
2. Open that address in your browser.
3. In the sidebar, choose **Kolkata saved historical data** to use the repository dataset, or **Upload your own CSV** to select your file.
4. View the predictions and download the result CSV.

**Important offline notes**

- Install dependencies before going offline.
- The historical file expected by the project is `data/raw/kolkata_traffic_weather.csv`. Make sure it is included in your downloaded copy.
- If the trained model artifact is not present, the CSV page attempts to prepare it from the included historical dataset. That requires the dataset and the ML dependencies.
- Do not use `frontend/app.py` for offline mode: it is the online dashboard and expects the FastAPI backend for live data.
- Offline mode does not show live traffic/weather and does not need TomTom/OpenWeather API keys.
- Map background tiles and externally hosted fonts are not available offline; the prediction workflow itself is local.

## 4. Run the online application locally (optional)

Online mode needs working internet, API keys and two terminals.

### Terminal 1 — Start FastAPI

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
python backend/prepare_model.py
uvicorn app.main:app --app-dir backend --reload
```

Set the following environment variables before starting the backend (use your own valid keys; never paste keys into source code):

- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`

The backend's local health endpoint is `http://127.0.0.1:8000/health`.

### Terminal 2 — Start Streamlit

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501`. The frontend's default backend URL is `http://127.0.0.1:8000`. For other configuration options, see [frontend/README.md](frontend/README.md).

## 5. Online deployment

### FastAPI backend — Render

1. Connect this GitHub repository to Render.
2. Use the backend settings defined in [render.yaml](render.yaml).
3. Add `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` in Render's Environment settings.
4. Deploy the backend and confirm its `/health` endpoint responds.

The configured build command is:

```bash
pip install -r backend/requirements.txt && python backend/prepare_model.py
```

The configured start command is:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

### Streamlit frontend — Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/).
2. Sign in with GitHub and select this repository.
3. Set the main file path to `frontend/app.py`.
4. Add `BACKEND_URL` in App settings → Secrets, using your deployed Render backend URL.
5. Deploy the app.

Never put TomTom/OpenWeather keys in the Streamlit frontend. Keep those keys on the backend service only.

## 6. Repository structure

```text
traffic-congestion-prediction/
├── backend/                 # FastAPI app and API integration
│   ├── app/                 # API routes and services
│   ├── requirements.txt
│   └── prepare_model.py
├── frontend/                # Streamlit user interfaces
│   ├── app.py               # Online dashboard + CSV page
│   ├── local_app.py         # Local offline entry point
│   ├── csv_app.py           # CSV prediction interface
│   └── requirements.txt
├── ml/                      # ML implementation (.py files)
│   ├── main.py
│   ├── train_model.py
│   ├── random_forest_model.py
│   ├── csv_inference.py
│   └── requirements.txt
├── data/
│   └── raw/                 # Historical Kolkata dataset
├── documentation/           # Reports, presentation and screenshots
├── other-files/             # Supporting project files and tests
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Root / complete project dependencies
└── README.md
```

## 7. Model performance — read carefully

The team has reported **83.33% accuracy** from a previous test. That test output has not yet been independently verified in this repository. Other values below are estimates for documentation planning, not measured results.

| Metric | Value | Status |
|---|---:|---|
| Accuracy | **83.33%** | Team-reported; output not independently verified |
| Precision | **84.00%** | Estimated |
| Recall | **83.33%** | Estimated |
| F1-score | **83.66%** | Estimated |
| Macro F1-score | **83.50%** | Estimated |

An earlier held-out evaluation recorded in the repository reported 60.22% accuracy, 54.81% macro F1-score and a 79.77% majority-class baseline. This is a separate evaluation run and has not yet been reconciled with the later team-reported result. Do not combine results from different runs or describe estimated values as measured results.

The prediction target is approximately 15 minutes after the input observation timestamp. It is not necessarily 15 minutes after a user opens the dashboard. See [ml/README.md](ml/README.md) for model details.

## 8. Team collaboration

The team leader maintains the `main` branch. Other members should create their own feature branches, commit their changes and open Pull Requests. The team leader reviews and tests each Pull Request before merging it into `main`.

## 9. Security

- Never upload API keys, GitHub tokens, passwords or private credentials to GitHub.
- Store backend API keys in Render Environment settings or a local untracked `.env` file.
- Do not put secrets in screenshots, documentation or frontend code.
- If a key is accidentally committed, revoke/rotate it immediately.

## 10. Known limitations

- Kolkata is the initial target area; other-city performance has not been validated.
- Live information depends on TomTom/OpenWeather API coverage and availability.
- Offline mode uses saved data; it cannot provide live traffic or weather.
- The reported 83.33% accuracy and estimated supporting metrics must be verified against the exact held-out test output.
- The visitor counter is an approximate visit/session counter, not a verified count of unique people.

## Help

For component-specific setup and troubleshooting, open [frontend/README.md](frontend/README.md), [backend/README.md](backend/README.md), or [ml/README.md](ml/README.md).
