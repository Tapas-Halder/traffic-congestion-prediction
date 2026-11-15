# TrafficIQ Machine Learning — Kolkata

This folder contains the project's machine-learning implementation in Python `.py` files. The current model is a **Random Forest classifier** for congestion-level prediction using traffic and weather features.

## Data source and scope

- The initial geographic scope is Kolkata.
- Traffic observations are obtained from TomTom.
- Weather observations are obtained from OpenWeather.
- The project does not install or use physical roadside sensors.
- The historical source CSV is stored at repository level: `data/raw/kolkata_traffic_weather.csv`.

Do not describe API-derived observations as readings from sensors installed by this project.

## Folder layout

```text
ml/
├── main.py                 # ML workflow entry point
├── config.py               # Paths and model constants
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── analysis.py
│   ├── visualization.py
│   └── utils.py
├── requirements.txt
├── README.md
├── outputs/                # Generated charts/reports (if created)
├── clean_data.py           # Data cleaning
├── train_model.py          # Random Forest training and evaluation
├── random_forest_model.py  # Inference interface used by backend
└── test_model.py           # ML tests
```

The repository-level historical CSV is not duplicated under `ml/data/raw/`. Cleaned data and model artifacts are generated in the configured locations; check `ml/config.py` for the exact paths. Generated files may be ignored by Git.

## Setup and run

Run commands from the repository root:

```bash
pip install -r ml/requirements.txt
python -m ml.main all
python -m ml.main test
python -m ml.main analyze
```

Use the command supported by the current `ml/main.py` entry point. If a command fails, check its available options and the paths in `ml/config.py` rather than creating duplicate datasets or model files.

## Model target and evaluation

The documented prediction horizon is approximately **15 minutes after the input observation timestamp**. It is not necessarily 15 minutes from the current wall-clock time.

The recorded held-out evaluation currently documented by the project is:

| Metric | Result |
|---|---:|
| Accuracy | 60.22% |
| Macro F1-score | 54.81% |
| Majority-class baseline accuracy | 79.77% |

These figures are previously recorded results, not a claim that this README update reran training. In that evaluation, the Random Forest accuracy was below the majority-class baseline. The project must therefore be presented honestly as a prototype whose model still needs improvement. Do not claim high accuracy or production readiness.

Before reporting new results, rerun evaluation using a held-out test set and save the classification report, confusion matrix, class-wise precision/recall/F1 and the split details. Avoid evaluating on training data or tuning against the final test set.

## Backend compatibility

The FastAPI backend imports `ml.random_forest_model` and calls its `predict_congestion` inference function. Preserve that import path and function contract when changing the model code, or update and test the backend integration at the same time.

## Data and security

- Never place TomTom or OpenWeather API keys in ML source files.
- Never commit credentials or private tokens.
- Do not fabricate traffic/weather observations to increase dataset size or model scores.
- Keep training, evaluation and inference code in Python `.py` files; this project does not require Jupyter notebooks.
