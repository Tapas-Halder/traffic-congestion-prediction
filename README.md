# Traffic Congestion Prediction System

This implementation follows the supplied Traffic Congestion Prediction System document: live traffic -> historical/training data -> feature engineering -> ML model -> 15/30/45/60 minute congestion prediction -> traffic dashboard.

## Current implementation

- **Traffic source:** TomTom Routing/Traffic API for live route travel time, traffic delay and route geometry.
- **Weather source:** OpenWeather current conditions.
- **Feature engineering:** hour, day of week, weekend flag, 5/15/30/60 minute lag values, rolling mean/std, temperature, rainfall, visibility, event flag, congestion index and speed ratio.
- **ML:** Random Forest regressor for future speed + Random Forest classifier for Free Flow / Moderate / Heavy / Severe congestion.
- **Forecast horizons:** 15, 30, 45 and 60 minutes. The model is trained for the 15-minute horizon and recursively produces the longer horizons.
- **Confidence:** classifier probability.
- **Dashboard:** Kolkata route selector, live map, current congestion, live weather, previous observations, future timeline, alerts and model metrics.
- **Recent history:** browser localStorage keeps route observations, while FastAPI keeps recent observations during the running service. No fake previous live data is shown.

## Important data note

The training script creates a **synthetic sensor-style historical baseline** because no real Kolkata traffic-sensor history is included in the supplied project document/repository. This is suitable for demonstrating the complete ML pipeline, but real historical traffic CSV/sensor data should replace it before claiming production-level accuracy.

The model uses the historical feature structure required by the document. Real sensor data can later provide vehicle volume, occupancy, queue length, incidents, roadworks, holidays and other contextual fields.

## Local setup

Create `backend/.env` from `.env.example`:

```text
TOMTOM_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
FRONTEND_URL=*
```

Install and train:

```bash
pip install -r backend/requirements.txt
python ml/train_model.py
cd backend
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/`.

## Render

The repository is configured as one Render Web Service. Build command:

```text
pip install -r backend/requirements.txt && python ml/train_model.py
```

Start command:

```text
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Required Render environment variables:
- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`
- `PYTHON_VERSION=3.11.11`

Never commit API keys.

## API endpoints

- `GET /api/health`
- `GET /api/locations`
- `GET /api/route-predict?origin=...&destination=...`
- `GET /api/route-history?origin=...&destination=...`
- `GET /api/weather?lat=...&lon=...`
- `GET /api/model-metrics`
- `GET /docs`
