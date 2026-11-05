# Version 2 — Run Locally on a PC Completely Offline

This local version has only two features:

1. Use the real Kolkata historical CSV bundled in the repository.
2. Upload a CSV file stored on the same computer.

It does not start FastAPI and does not call TomTom, OpenWeather, Render or any other online service.

## One-time preparation (internet is needed)

A new computer needs internet to download the repository and install Python packages. Do these steps before disconnecting.

1. Download the ZIP from the GitHub repository, or clone it:

   ```powershell
   git clone https://github.com/Tapas-Halder/traffic-congestion-prediction.git
   cd traffic-congestion-prediction
   ```

2. Install Python 3.11. Open PowerShell inside the project folder.

3. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install the packages:

   ```powershell
   python -m pip install -r frontend/requirements.txt
   ```

5. Prepare the Random Forest model using the CSV bundled in the repository. This step does not call any API:

   ```powershell
   python backend/prepare_model.py
   ```

   Wait until the terminal reports that the model is ready. The model artifact is saved under `ml/artifacts/` on this PC.

## Run without internet

1. Disconnect Wi-Fi/Ethernet.
2. Activate the environment again if you opened a new PowerShell window:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Start the offline app:

   ```powershell
   python -m streamlit run frontend/local_app.py
   ```

4. Open the local URL shown in the terminal, usually `http://localhost:8501`.
5. Select either **Kolkata saved historical data** or **Upload your own CSV**.

Keep the terminal open while using the app. The app runs on your PC; it is not a public website.

## CSV columns

Required, case-sensitive columns:

```csv
timestamp_utc,location_id,current_speed_kmph,free_flow_speed_kmph,confidence,temperature_c,humidity_pct,rain_1h_mm
```

Optional columns: `latitude`, `longitude`, `time_zone`. Include a timezone marker in timestamps, for example `2026-10-18T10:00:00Z`.

## Offline limitations

- No current traffic or current weather can be fetched without internet.
- No TomTom/OpenWeather API calls are made.
- The map shows checkpoint markers without online background map tiles.
- Predictions use the bundled model and the data supplied by the historical CSV or uploaded CSV.
- The model predicts the congestion class approximately 15 minutes after each row's observation timestamp, not 15 minutes from the current clock time.
- If Python packages, the dataset or the trained model are missing, restore/install them before disconnecting from the internet.
