# Option A — CSV-first final demo (Kolkata)

This is the simplified, API-independent submission path. Existing FastAPI/Render code is retained; the previous dashboard is archived as `frontend/legacy_live_app.py`. The default `frontend/app.py` now opens the CSV dashboard.

## How to run locally

From the repository root, with Python 3.11 recommended:

```bash
python -m pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

No TomTom/OpenWeather keys and no Render server are required for CSV predictions. On first startup, if `ml/artifacts/congestion_model.joblib` is absent, the app calls the existing `backend/prepare_model.py` to train from `data/raw/kolkata_traffic_weather.csv`. That historical dataset must be available in the deployment. Training can take time. The model is cached per running process.

## Streamlit Community Cloud

Select repository `Tapas-Halder/traffic-congestion-prediction`, target branch after PR merge, and entrypoint `frontend/app.py`. Install dependencies from `frontend/requirements.txt`. No `BACKEND_URL` or external API secrets are required for the default CSV mode. If the repository dataset is missing, or training fails due to cloud resource limits, prepare the trusted model artifact offline and arrange a secure supported way to make it available to the deployment. Do not upload unknown `.joblib` files.

## Input CSV

Required headers (case-sensitive):

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional: `latitude,longitude` for map markers. Timestamps should use UTC ISO 8601, e.g. `2026-10-18T10:00:00Z`. Rows are historical observations. Speed must be nonnegative, free-flow speed positive, confidence 0–1, humidity 0–100, and rain nonnegative. Missing weather and confidence values can be imputed by the trained pipeline. Up to 25,000 rows per upload. Invalid rows are reported separately.

The app predicts Low / Moderate / Heavy for 15 minutes after **each input row's observation time**. It does **not** predict traffic 15 minutes from the current clock time unless current data is supplied, and it does not route between two destinations. The map displays predicted checkpoint markers, not continuous road segments. Example CSV values are illustrative only.

## Model & evaluation

The existing Random Forest pipeline uses 9 features, including Kolkata local hour and weekday, and its saved model bundle. Training targets are matched at 15 ± 5 minutes. Saved evaluation: accuracy 0.6022, macro F1 0.5481, majority baseline 0.7977. Do not advertise the model as highly accurate or the probability as calibrated confidence.

## Test

```bash
python -m unittest discover -s other-files/tests -p "test_csv_inference.py"
python ml/test_model.py
```

After merge, test local and cloud CSV upload, invalid rows, download, and map with valid coordinates. Check the deployment logs for model training and dependency errors. Tests have to be executed; adding a test file does not mean it passed.

## Team ownership

- Tapas Halder: integration, PR review, deployment and demo verification.
- Soumyadeep Mandal: Streamlit upload, table, map and download.
- Sumit Kumar Mandal: CSV validation and feature engineering.
- Subhajit Podder: model inference, testing and metrics.
- Pammi Biswas: documentation, screenshots, results and limitations.

## Security

Never commit API keys or untrusted serialized model artifacts. Rotate any previously exposed keys. This Option A workflow makes no external traffic/weather API calls.
