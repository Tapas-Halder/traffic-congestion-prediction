# Backend, data collection and machine learning

FastAPI, API collection, and the model-preparation helper live here; ML code is in the root `ml/` folder. No physical sensors.

## Local setup (run from repository root)

```bash
python -m pip install -r backend/requirements.txt
python backend/prepare_model.py
uvicorn app.main:app --app-dir backend --reload
```

Set `TOMTOM_API_KEY` and `OPENWEATHER_API_KEY` as environment variables. See `backend/.env.example`. Never commit keys.

## ML and offline tests

```bash
python ml/clean_data.py
python ml/train_model.py
python ml/test_model.py
python other-files/tests/test_integration.py
```

The historical dataset is `data/raw/kolkata_traffic_weather.csv`. The trained model artifact is generated under `ml/artifacts/`. `backend/prepare_model.py` automates cleaning and training.

## API endpoints

- `GET /health`
- `GET /api/v1/model/status`
- `GET /api/v1/data/current?latitude=22.5726&longitude=88.3639`
- `POST /api/v1/predict` with JSON `{"latitude":22.5726,"longitude":88.3639}`
- `GET /api/v1/route` with `from_lat`, `from_lon`, `to_lat`, `to_lon`

## Deployment

Render build: `pip install -r backend/requirements.txt && python backend/prepare_model.py`

Render start: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`

Streamlit: `frontend/app.py` with `frontend/requirements.txt`.

The previous GitHub Actions workflows are saved in `Backup`. Automatic data collection is paused.
