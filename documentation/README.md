# TrafficIQ Documentation

This folder is for the project's written report, presentation and supporting submission material.

## Project scope

TrafficIQ is an initial Kolkata-focused traffic congestion prediction prototype. It uses real-world traffic observations from TomTom and weather observations from OpenWeather. It does not use physical roadside sensors.

The project includes a FastAPI backend, Streamlit frontend and a Python Random Forest machine-learning workflow. The online dashboard depends on the external APIs and deployed backend. CSV prediction and local saved-data workflows use data supplied by the user or stored in the repository.

## Documentation should cover

- Project objective, Kolkata scope and intended users
- Data sources and the fact that API observations are not physical sensor readings
- System architecture and data flow
- FastAPI endpoints and external API integration
- Data preparation, features, target definition and prediction horizon
- Random Forest training, testing and evaluation
- Streamlit online and CSV-upload interfaces
- Local/offline setup and online deployment
- Testing evidence, screenshots and known limitations
- Team roles and future improvements

## Model evaluation — important

The current repository records the following held-out evaluation:

| Metric | Recorded result |
|---|---:|
| Accuracy | 60.22% |
| Macro F1-score | 54.81% |
| Majority-class baseline accuracy | 79.77% |

The recorded model accuracy is below the majority-class baseline. Explain this honestly in the report. Do not call the model highly accurate, do not claim it beats the baseline, and do not describe it as production-ready. These are previously documented figures; rerun the evaluation and save fresh outputs before presenting them as final test results.

The prediction horizon is approximately 15 minutes after the input observation timestamp. Make this distinction clear in the report.

## Screenshots and test evidence

Only include genuine screenshots captured from the running application. For each test, record what was tested, the input, expected result, actual result and pass/fail status. Do not invent test outcomes, screenshots or metrics.

## Project files

The report and presentation should be stored in this folder once they have actually been added to the repository. Check the repository file list before stating that a document or presentation is included.

## Team responsibilities

- Tapas Halder — Team Leader; Backend and API Integration
- Soumyadeep Mandal — Frontend Developer
- Sumit Kumar Mandal — ML Developer; Data Preparation
- Subhajit Podder — ML Developer; Model Training and Evaluation
- Pammi Biswas — Documentation

Add mentor details only after confirming the correct name and spelling.
