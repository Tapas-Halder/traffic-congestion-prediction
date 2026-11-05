# Project Documentation

## Project
Kolkata Traffic Congestion Prediction System

## The two supported versions

### 1. Online — Live Kolkata + CSV Upload
- Streamlit Community Cloud frontend.
- FastAPI backend deployed on Render.
- TomTom Traffic API supplies live traffic observations.
- OpenWeather API supplies current weather observations.
- CSV Upload page accepts a traffic/weather CSV and generates ML predictions.

### 2. Local PC — Completely Offline
- Download the repository and dataset to a computer.
- Install Python dependencies and prepare the model once.
- Run `frontend/local_app.py` locally.
- Choose either the bundled Kolkata historical dataset or a local CSV upload.
- No FastAPI server, API keys, TomTom, OpenWeather or internet connection is used while running the prepared local application.

## ML workflow
1. Historical observations are stored in `data/raw/`.
2. Python scripts in `ml/` clean data and create features.
3. `ml/train_model.py` trains the Random Forest model.
4. `ml/csv_inference.py` validates uploaded CSV rows and predicts congestion.
5. Predictions represent the target approximately 15 minutes after each observation timestamp.

## Documentation checklist
- [ ] Problem statement, scope and objectives
- [ ] Architecture and data flow diagrams for both versions
- [ ] Data collection and dataset description
- [ ] Preprocessing and feature engineering
- [ ] ML methodology and evaluation metrics
- [ ] Online backend API endpoints and error handling
- [ ] Screenshots of online and offline workflows
- [ ] Deployment and local offline setup guides
- [ ] Test cases and actual test results
- [ ] Limitations and team contributions

API credentials must remain in private deployment environment variables and must never be committed to GitHub.
