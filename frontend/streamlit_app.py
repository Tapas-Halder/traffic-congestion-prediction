import os

import requests
import streamlit as st

API_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Kolkata Traffic Prediction", page_icon="🚦", layout="wide")

st.title("🚦 Kolkata Traffic Congestion Prediction")
st.caption("TomTom traffic + OpenWeather + Random Forest through FastAPI")

st.sidebar.header("FastAPI")
st.sidebar.code(API_URL)

latitude = st.number_input("Latitude", value=22.5726, format="%.6f")
longitude = st.number_input("Longitude", value=88.3639, format="%.6f")

col1, col2 = st.columns(2)

with col1:
    if st.button("Check Current Traffic & Weather", use_container_width=True):
        try:
            response = requests.get(
                f"{API_URL}/api/v1/data/current",
                params={"latitude": latitude, "longitude": longitude},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            traffic = data.get("traffic", {}).get("flowSegmentData", {})
            weather = data.get("weather", {})
            main = weather.get("main", {})

            st.subheader("Current Data")
            st.metric("Current Speed", f"{traffic.get('currentSpeed', 'N/A')} km/h")
            st.metric("Free-flow Speed", f"{traffic.get('freeFlowSpeed', 'N/A')} km/h")
            st.metric("Temperature", f"{main.get('temp', 'N/A')} °C")
            st.metric("Humidity", f"{main.get('humidity', 'N/A')} %")
            st.write("Weather:", (weather.get("weather") or [{}])[0].get("description", "N/A"))
        except requests.RequestException as exc:
            st.error(f"FastAPI connection/API error: {exc}")

with col2:
    if st.button("Predict Congestion", type="primary", use_container_width=True):
        try:
            response = requests.post(
                f"{API_URL}/api/v1/predict",
                json={"latitude": latitude, "longitude": longitude},
                timeout=30,
            )
            if response.status_code == 503:
                st.warning("ML model is not connected yet. Ask the ML team to add random_forest_model.py.")
            response.raise_for_status()
            result = response.json()

            st.subheader("Prediction")
            st.success(result.get("prediction", "N/A"))
            confidence = result.get("confidence")
            if confidence is not None:
                st.metric("Model Confidence", f"{confidence * 100:.1f}%")
            st.caption(f"Source: {result.get('source', 'N/A')}")
        except requests.RequestException as exc:
            st.error(f"Prediction/API error: {exc}")
