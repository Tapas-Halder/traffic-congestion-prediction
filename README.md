# Traffic Congestion Prediction System

Simple Kolkata-focused traffic congestion prediction system.

## Technology
- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- Traffic data: TomTom API
- Weather data: OpenWeather API
- Machine Learning: Python
- Version control: GitHub

## Project scope
The first version focuses on Kolkata city and uses real-world external API data instead of physical sensors.

## Team
- Team Leader / Backend & API
- ML: Sumit, Podder
- Frontend & Documentation: Soumodip, Pammi

## Current project structure
```
traffic-congestion-prediction/
├── backend/
├── frontend/
├── ml/
├── data/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## Important
API keys must never be committed to GitHub. Store them in local environment variables using `.env`.

## Development plan
1. Connect TomTom and OpenWeather APIs in FastAPI.
2. Prepare a simple real-world dataset.
3. Train and evaluate the first ML model.
4. Create prediction API endpoint.
5. Connect the existing frontend.
6. Test the complete data flow.
