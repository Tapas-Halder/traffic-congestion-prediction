# Traffic Congestion Prediction System

Kolkata-focused traffic congestion prediction using real-world TomTom traffic and OpenWeather data. No physical sensors are used.

## Data pipeline
TomTom + OpenWeather -> `data/raw/kolkata_traffic_weather.csv` -> `ml/clean_data.py` -> `data/processed/kolkata_traffic_weather_clean.csv` -> Random Forest -> FastAPI -> Streamlit.

## ML Python files
- `ml/clean_data.py`: validates columns, normalizes types, removes duplicate location/timestamp rows, writes processed CSV.
- `ml/train_model.py`: trains/evaluates a Random Forest with chronological train/test split.
- `ml/random_forest_model.py`: required FastAPI model entry point.
- `ml/predict.py`: helper for direct model use.
- `ml/test_model.py`: checks model artifact loading.

## Local commands
```bash
python -m pip install pandas scikit-learn joblib
python ml/clean_data.py --input data/raw/kolkata_traffic_weather.csv --output data/processed/kolkata_traffic_weather_clean.csv
python ml/train_model.py
python ml/test_model.py
```

The trained artifact is written to `ml/artifacts/congestion_model.joblib` and is not committed. Train it in the backend deployment environment or provide the artifact through your deployment process.

## Model limitations
The target is the congestion class at the next available observation for the same location. Labels are proxies derived from speed ratio: >=0.90 Low, >=0.70 Moderate, otherwise Heavy. This is not independent ground truth, and the prediction horizon depends on collection interval. Do not claim a fixed 15-minute forecast unless the timestamps validate it. Evaluate per-class precision/recall as well as accuracy.

## FastAPI contract
`ml/random_forest_model.py` exposes `predict_congestion(features: dict[str, float])` and returns `(label, confidence)`. Required keys: `current_speed`, `free_flow_speed`, `speed_ratio`, `traffic_confidence`, `temperature`, `humidity`, `rain_1h`, `hour`, `day_of_week`.

Keep API keys in GitHub Actions Secrets or local ignored `.env`; never commit secrets. Work on a feature branch and open a Pull Request for team-leader review.
