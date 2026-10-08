# Phase 4 — API Data Collection

Collects real-life Kolkata traffic and weather data using external APIs.

## APIs
- TomTom Traffic Flow API — traffic speed/flow information.
- OpenWeather Current Weather API — current weather information.

No physical traffic sensors are required for this simple version.

## Setup

From the repository root:

    cd backend
    python -m venv .venv
    pip install -r requirements.txt

Copy the root .env.example to .env and add your API keys locally. Never commit .env.

Example .env values:

    TOMTOM_API_KEY=your_key_here
    OPENWEATHER_API_KEY=your_key_here
    CITY=Kolkata
    LATITUDE=22.5726
    LONGITUDE=88.3639
    REQUEST_TIMEOUT=10

## Run

    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs.

## Endpoints
- GET /health
- GET /api/v1/data/current
- GET /api/v1/data/current?latitude=22.5726&longitude=88.3639

## Phase 4 data flow
TomTom API + OpenWeather API -> Python services -> collector -> FastAPI -> frontend/ML


## Phase 5 - Backend prediction API

The backend now exposes:
- GET /health - backend and API-key configuration status.
- GET /api/v1/data/current - live TomTom + OpenWeather payload.
- POST /api/v1/predict - collects live data, builds ML features, and runs MODEL_PATH.

### ML model contract

The trained model is loaded with joblib and receives these features in this exact order:
current_speed, free_flow_speed, speed_ratio, traffic_confidence, temperature, humidity, rain_1h, hour, day_of_week.

Set MODEL_PATH to the ML team's .joblib model file after training. Until the model exists, /api/v1/predict returns HTTP 503 rather than inventing a prediction.

### Local test

    cd backend
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # Linux/macOS: source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs and test the endpoints from Swagger UI.
