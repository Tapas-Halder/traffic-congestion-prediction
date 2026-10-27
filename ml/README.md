# TrafficIQ Machine Learning — Kolkata

This module uses **real TomTom/OpenWeather observations** and a Python **Random Forest classifier** to predict congestion 15 minutes ahead. No sensors and no fabricated traffic values.

## Folder layout

```text
ml/
├── main.py                 # Entry point
├── config.py               # Paths and constants
├── data/
│   ├── raw/                # Optional local ML staging area (source CSV remains at root data/raw/)
│   └── processed/          # Optional local staging area
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── analysis.py
│   ├── visualization.py
│   └── utils.py
├── requirements.txt
├── README.md
├── outputs/                 # Generated charts/reports (not committed)
├── clean_data.py           # Existing validated cleaning implementation
├── train_model.py          # Existing 15-minute Random Forest training
├── random_forest_model.py  # Backend inference contract; do not delete
└── test_model.py           # ML smoke tests
```

The real historical dataset is **`data/raw/kolkata_traffic_weather.csv` at the repository root**. We deliberately do not duplicate the 10,000+ row CSV inside `ml/data/raw/`. The cleaned CSV is written to root `data/processed/` and the trained model to `ml/artifacts/`. Both are generated and ignored by Git. This preserves compatibility with FastAPI and Render.

From the repository root:

```bash
pip install -r ml/requirements.txt
python -m ml.main all
python -m ml.main test
python -m ml.main analyze
```

To create a histogram of real recorded speeds:

```python
from ml.config import RAW_CSV
from ml.src.visualization import save_speed_plot
save_speed_plot(RAW_CSV, "ml/outputs/speed_distribution.png")
```

The backend still imports `ml.random_forest_model` and its `predict_congestion` function. Never put API keys in ML code or commit generated models.
