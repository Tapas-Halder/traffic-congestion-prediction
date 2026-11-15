# TrafficIQ — Kolkata Traffic Congestion Prediction System

A simple machine-learning project that estimates road congestion in **Kolkata, India**, using real traffic and weather observations from external APIs. The project does **not** use physical roadside sensors.

| Item | Project setup |
|---|---|
| Initial scope | Kolkata city |
| Traffic source | TomTom Traffic API |
| Weather source | OpenWeather API |
| Prediction model | Random Forest classifier |
| Prediction horizon | Approximately 15 minutes after an observation |
| Backend | FastAPI |
| Frontend | Streamlit |
| Online deployment | FastAPI on Render; Streamlit Community Cloud |
| ML implementation | Python `.py` files |

## What the project does

1. The online dashboard requests current traffic information from TomTom and weather information from OpenWeather through the FastAPI backend.
2. The backend prepares the model input and obtains a congestion prediction.
3. Streamlit presents the current information and prediction in a user-friendly dashboard.
4. A separate CSV page lets a user upload a dataset and generate predictions.
5. The local application can use the historical dataset included in the repository or a CSV selected by the user, without calling the live APIs.

**Important:** an API observation is real-world data, but it is not a physical sensor installed by this project. Data availability and coverage depend on the external providers.

## Main features

- Live Kolkata traffic and weather view (when the APIs and backend are available).
- ML-based congestion prediction.
- CSV upload and prediction with downloadable results.
- A local mode that uses files already downloaded to the computer.
- A visitor counter for the public dashboard (where its backend storage is configured).

## Project architecture

```text
ONLINE
TomTom Traffic API ─────┐
                        ├──> FastAPI backend ──> Random Forest model
OpenWeather API ────────┘              │
                                       v
                               Streamlit dashboard

CSV upload ──> preprocessing ──> ML model ──> prediction results

LOCAL
Saved historical CSV / user CSV ──> local Streamlit app ──> ML model
```

The local mode does not fetch live traffic or weather. To run it without internet, first download the repository and install its Python dependencies while internet access is available.

## Model performance — reported result and estimates

The team has reported **83.33% accuracy** from a previous test. The test output has not yet been independently checked in this repository. The other values below are **estimates for documentation planning**, not metrics calculated from the test predictions.

| Metric | Value | Status |
|---|---:|---|
| Accuracy | **83.33%** | Team-reported; test output not yet verified |
| Precision | **84.00%** | Estimated |
| Recall | **83.33%** | Estimated |
| F1-score | **83.66%** | Estimated |
| Macro F1-score | **83.50%** | Estimated |

**Important:** Do not describe the estimated precision, recall or F1 values as measured results. They must be replaced with the actual values from a held-out test evaluation before making a final performance claim.

For context, an earlier held-out evaluation already recorded in this repository reported 60.22% accuracy, 54.81% macro F1-score and a 79.77% majority-class baseline. That is a separate recorded evaluation and has not been reconciled with the team's later-reported 83.33% result. Keep the two test runs distinct until their datasets, split method and output reports are compared.

Accuracy alone can be misleading when congestion classes are imbalanced. Before final submission, rerun evaluation on a held-out test set and preserve the classification report, confusion matrix, test date/split details and output file. Do not change or inflate measured metrics to make the result look better.

The prediction target is tied to the input observation timestamp: approximately 15 minutes after that observation. It does not necessarily mean 15 minutes from the time a user opens the dashboard. Model performance and data coverage outside Kolkata have not been established.

## Repository structure

```text
.
├── backend/                 # FastAPI app and external API integrations
├── frontend/                # Streamlit online, CSV and local interfaces
├── ml/                      # Python ML preprocessing, training and inference
├── data/
│   ├── raw/                 # Historical source data
│   └── processed/           # Generated cleaned data (if created)
├── documentation/           # Project report, presentation and supporting docs
└── README.md
```

See the README files inside `backend/`, `frontend/`, and `ml/` (where present) for component-specific instructions. Generated model artifacts and processed files may be created during setup and are not necessarily committed to Git.

## Online deployment

### FastAPI backend — Render

Configure the service using the actual backend entry point and requirements file in the repository. Set the following environment variables in Render's Environment settings:

- `TOMTOM_API_KEY`
- `OPENWEATHER_API_KEY`
- `CITY=Kolkata`
- `LATITUDE=22.5726`
- `LONGITUDE=88.3639`

Use the repository's current Render start/build configuration. Do not copy API keys into source code, README files, screenshots, or Git commits.

### Streamlit frontend — Streamlit Community Cloud

Deploy the Streamlit entry-point file configured for the online application. Set its backend URL using Streamlit Secrets (for example, `BACKEND_URL`) to the deployed FastAPI service URL. The exact entry-point path should match the current repository configuration.

## Local run

The local-only interface is intended to run with saved data and the locally available model/dependencies. First clone or download the repository and install dependencies while online. Then follow the current local instructions in the frontend and ML README files. Do not expect live TomTom/OpenWeather data when offline.

## Data and privacy

- Never commit API keys, GitHub tokens, passwords or other secrets.
- Keep secrets in Render Environment settings or the relevant deployment secret manager.
- Use only the columns and formats accepted by the current CSV prediction implementation; consult the frontend/ML instructions before preparing a CSV.
- External API availability, rate limits and data licensing/coverage may affect live results.

## Visitor counter

The visitor counter is an approximate application visit/session counter, not a verified count of unique people. When `VISITS_GITHUB_TOKEN` is configured on the FastAPI backend, each new browser session updates `data/visits.json` directly on the repository's `main` branch using the GitHub Contents API. Visitor-count updates do not create Pull Requests and do not use a separate data branch.

Configure these variables in the Render backend environment:
- `VISITS_GITHUB_TOKEN`: fine-grained GitHub token with Contents read/write permission for this repository.
- `VISITS_GITHUB_REPO`: `Tapas-Halder/traffic-congestion-prediction` (optional default).
- `VISITS_GITHUB_PATH`: `data/visits.json` (optional default).

If you previously added `VISITS_GITHUB_BRANCH`, remove that old environment variable; the counter always writes to `main`. Keep the token only in Render Environment settings and never commit it or put it in Streamlit frontend secrets. Without the token, local SQLite storage is used instead. GitHub API rate limits apply, so this is suitable for a small project/demo counter, not high-traffic production analytics.

## Team collaboration

The team leader maintains the main branch. Other members should work on separate branches, commit their changes and open Pull Requests. The team leader reviews and tests each change before merging it into `main`.

## Limitations and future improvements

- The currently recorded model evaluation is below the majority-class baseline.
- Model quality depends on the amount, quality, balance and representativeness of historical observations.
- External API coverage and availability can vary by road and time.
- Kolkata is the initial target area; other-city performance is not validated.
- Future work should focus on stronger time-aware validation, class-wise metrics, better balanced training data, comparison with simple baselines, and more historical observations.

## Project status

This is an academic prototype demonstrating an API-connected traffic dashboard and a machine-learning workflow. Report only tests that were actually run, and use genuine screenshots from the running application as submission evidence.
