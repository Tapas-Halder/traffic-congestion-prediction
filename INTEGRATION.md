# Kolkata integration runbook

This branch combines the FastAPI backend, the Python-only Random Forest model, and the Streamlit frontend. No live keys are committed.

## 1. Install

From the repository root (Python 3.11 recommended):

```bash
python -m venv .venv
# Activate .venv for your operating system
python -m pip install -r backend/requirements.txt
python -m pip install -r frontend/requirements.txt
```

## 2. Train on the actual collected CSV

```bash
python ml/clean_data.py
python ml/train_model.py
python ml/test_model.py
```

Training writes `ml/artifacts/congestion_model.joblib`. This binary artifact is NOT fabricated or embedded in GitHub. It must be generated from sufficient real observations (at least 30 usable 15-minute pairs, and at least two training classes). If training fails due to insufficient pairs, keep collecting data at a regular interval and retry. Do not pretend predictions are available.

## 3. Start FastAPI

Put TOMTOM_API_KEY and OPENWEATHER_API_KEY in environment variables or in a local `.env` file (never commit secrets). From the repo root:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`. The health endpoint only checks backend responsiveness and key configuration, not live API or model readiness.

## 4. Start Streamlit (separate terminal)

```bash
cd frontend
streamlit run app.py
```

Set BACKEND_URL to the reachable FastAPI base URL if the backend is not local. Open `http://localhost:8501`. The historical chart reads `data/raw/kolkata_traffic_weather.csv` from the repo by default.

## 5. Integration checks

```bash
python tests/test_integration.py
python ml/test_model.py
```

The first test mocks external APIs and model inference. A passing offline test is not proof that live keys, external API quota, the trained artifact, or deployment work. Test one live location and prediction before merging/deploying.

## Shared conventions

- Model output: Low / Moderate / Heavy (future 15-minute congestion prediction).
- Live traffic classification uses speed/free-flow ratios: Low >= 0.90, Moderate >= 0.70, otherwise Heavy.
- Features `hour` and `day_of_week` are in Asia/Kolkata time.
- Model and frontend source files are integrated on this branch; team source branches are not rewritten.
- Deploy Streamlit and FastAPI as separately running services; set BACKEND_URL in the Streamlit environment.
