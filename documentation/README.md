# Project Documentation

## Project
Kolkata Traffic Congestion Prediction System

## Overview
This project uses historical traffic and weather observations from TomTom and OpenWeather to train a Python Random Forest model for 15-minute-ahead congestion classification.

## Architecture
1. Data collection: TomTom Traffic API and OpenWeather API.
2. Data storage: historical CSV in `data/raw/`.
3. Data cleaning and feature engineering: Python scripts in `ml/`.
4. ML training and evaluation: `ml/train_model.py` and `ml/test_model.py`.
5. Backend: FastAPI in `backend/`.
6. Frontend: Streamlit in `frontend/`.

## Deployment
- Backend: Render (check environment variables and model artifact before demo).
- Frontend: Streamlit Community Cloud.
- API credentials must be configured through deployment secrets/environment variables, never committed.

## Submission documentation checklist
- [ ] Problem statement, scope and objectives
- [ ] Architecture and data flow diagram
- [ ] Data collection and dataset description
- [ ] Preprocessing and feature engineering
- [ ] ML methodology, chronological split and evaluation metrics
- [ ] Backend API endpoints and error handling
- [ ] Frontend screenshots and user workflow
- [ ] Deployment and configuration guide
- [ ] Test cases and actual test results
- [ ] Limitations, future improvements and team contributions

## Source code
See the repository root README and the `backend/`, `frontend/`, and `ml/` folders.
