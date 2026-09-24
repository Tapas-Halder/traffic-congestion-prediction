# Traffic Congestion Prediction System

End-to-end traffic congestion prediction system with HTML/CSS/JS frontend, FastAPI backend, PostgreSQL/SQLite database, ML Random Forest baseline, TomTom Traffic API and OpenWeather API.

## Architecture
Frontend -> FastAPI -> external traffic/weather APIs + database -> ML prediction

The implementation follows the project guidelines: Python scripts only, modular folders, configuration through environment variables, and no committed secrets.

## Local run
1. Backend: `cd backend && python -m venv .venv && pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add API keys.
3. Train: `python ml/train_model.py`
4. Start: `cd backend && uvicorn main:app --reload`
5. Open `frontend/index.html` and change API_BASE in `frontend/app.js` to the backend URL.

## Render
The repository contains `render.yaml`. Create the Blueprint from GitHub, then set TOMTOM_API_KEY, OPENWEATHER_API_KEY and FRONTEND_URL in the Render service environment. Render creates PostgreSQL and DATABASE_URL automatically from the blueprint.

## Vercel
Import the `frontend` directory as a Vercel project. After the Render backend is live, replace YOUR-RENDER-SERVICE.onrender.com in `frontend/app.js` with the real Render URL.

Never commit `.env` or real API keys.
