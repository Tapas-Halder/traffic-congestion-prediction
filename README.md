# Traffic Congestion Prediction System

Simple final-year project based on the provided project guidelines.

## Parts
1. Frontend: HTML, CSS, JavaScript + Leaflet map
2. Backend: FastAPI
3. ML: Random Forest
4. External APIs: TomTom Traffic API + OpenWeather API

## Database
A database is **not required** for the basic project because the main requirement is live traffic data -> preprocessing/features -> ML prediction -> dashboard. Prediction results are returned directly by FastAPI and are not permanently stored.

## Flow
TomTom Traffic API + Weather API
        ↓
FastAPI
        ↓
Feature preparation
        ↓
Random Forest ML
        ↓
Congestion Level + Predicted Speed
        ↓
HTML/CSS/JS Dashboard

## Local setup
Create `backend/.env` from `.env.example`:

```text
TOMTOM_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
FRONTEND_URL=*
```

Install and run:

```bash
cd backend
pip install -r requirements.txt
cd ..
python ml/train_model.py
cd backend
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` for the full website and `http://127.0.0.1:8000/docs` for the API documentation.

## Single Render deployment
The full website is deployed as **one Render Web Service**. FastAPI serves the frontend files, so Vercel is not required.

Use `render.yaml` and set these Render environment variables:
- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`

`FRONTEND_URL` is already configured as `*` in `render.yaml` for the simple single-service setup.

After deployment, the Render URL opens the dashboard directly. No frontend URL needs to be added to `frontend/app.js` because it uses the same-origin API.

Never commit `.env` or API keys.