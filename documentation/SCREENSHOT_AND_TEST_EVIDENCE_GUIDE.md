# TrafficIQ — Screenshot and Test Evidence Guide

## Purpose
The project submission requires **real** screenshots and test evidence. This folder must not contain generated/mock dashboard screenshots or invented test passes. Capture from the actual Streamlit app, Render/FastAPI endpoints and your Windows terminal.

## Required captures
Create `documentation/screenshots/` and save:
1. `01_kolkata_dashboard.png` — public Streamlit Traffic dashboard, default Kolkata, visible 15-minute result.
2. `02_roads.png` — Roads section and Low/Moderate/Heavy road conditions.
3. `03_kolkata_map.png` — Map with actual Kolkata checkpoint markers.
4. `04_route.png` — Route tab with start/end selection and visible route result (or honest unavailable state).
5. `05_csv_prediction.png` — CSV upload and readable 15-minute prediction.
6. `06_global_csv_map.png` — real non-Kolkata sample CSV with latitude/longitude and visible mapped checkpoint.
7. `07_local_offline.png` — local-only Streamlit entrypoint and historical CSV prediction.
8. `08_api_health.png` — Render /health response; hide tokens and secrets.
9. `09_tests.png` — real terminal test results or GitHub Actions successful run.

## Windows steps
1. Open the working screen.
2. Press **Windows + Shift + S** and drag to capture the relevant section.
3. Open Paint, press **Ctrl + V**, save PNG with the exact filename.
4. Repeat for the nine items. Keep browser address or terminal command visible where safe.
5. In GitHub, open the repository, navigate to `documentation/`, create/open `screenshots/` and use **Add file → Upload files**. Commit to a documentation branch and open a PR.
6. Add each real screenshot to the final Word report (Insert → Pictures), below section 10, with a caption describing what it proves. Do not label a screenshot PASS if the feature failed.

## Test log template
Create `documentation/FINAL_TEST_RESULTS.md` and record for each test:
- UTC date/time and tested commit SHA
- Environment (local Windows / Render / Streamlit Cloud)
- Test name and exact command or user action
- Expected behavior and actual behavior
- PASS / FAIL / NOT TESTED
- Screenshot filename or link

Commands from repository root:

```powershell
git rev-parse HEAD
python -m compileall -q frontend backend ml
python -m unittest discover -s other-files/tests -p "test_csv_inference.py" -v
python backend/prepare_model.py
python ml/test_model.py
```

Do not publish API keys, Streamlit secrets, private paths, or other credentials in screenshots. Check repository size and data licensing before submitting a source ZIP.

## What is already measured?
`documentation/ML_EVALUATION_RESULTS.json` records 60.22% accuracy, 54.81% macro F1, and 79.77% majority-class baseline accuracy on 2,916 test rows. These are existing evaluation results, **not** evidence of a new successful test run.

## Full source code
The complete source is maintained separately at:
https://github.com/Tapas-Halder/traffic-congestion-prediction

For a ZIP, use GitHub **Code → Download ZIP** after the final PRs are merged. Record the final commit SHA in the report and test log.
