# Traffic Congestion Prediction System

Simple final-year project based on the provided project guidelines.

## Parts
1. Frontend: HTML, CSS, JavaScript + Leaflet map
2. Backend: FastAPI
3. ML: Random Forest
4. External APIs: TomTom Traffic API + OpenWeather API

## Database
A database is **not required** for the basic project because the main requirement is live traffic data -> preprocessing/features -> ML prediction -> dashboard. Removing PostgreSQL makes the project easier to understand, run and deploy. Prediction results are returned directly by FastAPI and are not permanently stored.

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

```
TOMTOM_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
FRONTEND_URL=*
```

Install and run:

```
cd backend
pip install -r requirements.txt
cd ..
python ml/train_model.py
cd backend
uvicorn main:app --reload
```

Open the frontend and set the Render/backend URL in `frontend/app.js`.

## Render
Use `render.yaml`. Set these environment variables in Render:
- TOMTOM_API_KEY
- OPENWEATHER_API_KEY
- FRONTEND_URL

No PostgreSQL/database setup is needed.

## Vercel
Deploy the `frontend` folder. After Render gives the backend URL, replace the placeholder URL in `frontend/app.js`.

Never commit `.env` or API keys.
