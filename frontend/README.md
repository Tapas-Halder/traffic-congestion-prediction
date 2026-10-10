# 🚦 TrafficIQ — Streamlit Dashboard

Traffic Congestion Prediction System built with Streamlit.

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Open in browser
```
http://localhost:8501
```

---

## Project Structure

```
trafficiq_streamlit/
│
├── app.py              ← Main Streamlit app
├── requirements.txt    ← Python dependencies
├── README.md           ← This file
│
└── (when you add ML model)
    ├── model/
    │   ├── xgboost_model.pkl
    │   └── lstm_model.h5
    └── data/
        └── historical_traffic.csv
```

---

## Features

| Tab | What it shows |
|---|---|
| 📊 Overview | Congestion gauge, speed trend chart, weather widget, recommendation |
| 🛣️ Roads | Live road cards, speed comparison bar chart |
| 🗺️ Map | Folium dark map with color-coded road overlays |
| 🔍 Route | From → To route search with live traffic applied |
| ⚙️ Pipeline | ML pipeline stages, model accuracy, feature importances |

---

## Connecting Your ML Model

Replace the `get_live_roads()` function with your real model:

```python
import pickle
import pandas as pd

# Load your trained model
model = pickle.load(open('model/xgboost_model.pkl', 'rb'))

def get_live_roads(horizon="Right now"):
    # Extract real features from your sensor data
    features = extract_features(horizon)
    
    # Run prediction
    predictions = model.predict(features)
    
    # Return in the same format the dashboard expects
    roads = []
    for i, r in enumerate(BASE_ROADS):
        speed  = int(predictions[i])
        status = speed_to_status(speed)
        roads.append({**r, "speed": speed, "status": status, "volume": ...})
    return roads
```

---

## Connecting TomTom API

```python
TOMTOM_KEY = "your_api_key_here"

def get_real_traffic(lat, lon):
    url = (f"https://api.tomtom.com/traffic/services/4/"
           f"flowSegmentData/absolute/10/json"
           f"?point={lat},{lon}&key={TOMTOM_KEY}")
    r = requests.get(url)
    data = r.json()["flowSegmentData"]
    return {
        "current_speed":   data["currentSpeed"],
        "freeflow_speed":  data["freeFlowSpeed"],
        "confidence":      data["confidence"]
    }
```

---

## Deploy to Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Set main file: `app.py`
5. Click Deploy — live URL in 2 minutes!
