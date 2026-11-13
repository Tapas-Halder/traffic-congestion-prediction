"""TrafficIQ CSV upload page: simple, local ML predictions from user data."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.csv_inference import REQUIRED, OPTIONAL, predict_csv
from ml.random_forest_model import MODEL_PATH, load_model

OFFLINE_MODE = os.getenv("TRAFFICIQ_OFFLINE_MODE", "").strip() == "1"
MAP_TILES = None if OFFLINE_MODE else "OpenStreetMap"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp{background:radial-gradient(ellipse at 15% 0%,#142c49 0%,#08111f 45%,#070d18 100%);color:#edf5ff;font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#101d30;border-right:1px solid #263850}
.block-container{max-width:1400px;padding-top:2.2rem;padding-bottom:3rem}
[data-testid="stHorizontalBlock"]{gap:1.25rem}
[data-testid="stVerticalBlock"]{gap:1rem}
.upload-guide,.result-card{margin:12px 0 20px}
div[data-testid="stMetric"]{margin:5px 0 10px}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;color:#f3f8ff;letter-spacing:-.03em}
h1{font-size:2.25rem!important} p,label{color:#a9bad0}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#17283e,#101c2d);border:1px solid #2a405b;padding:16px;border-radius:15px}
div[data-testid="stMetricValue"]{color:#f3f8ff;font-family:'Space Grotesk',sans-serif}
.stButton>button,.stDownloadButton>button{border-radius:10px;background:linear-gradient(110deg,#1768b4,#258fc4);border:1px solid #3977b7;color:white;font-weight:700;min-height:42px}
.stAlert{border-radius:12px}[data-testid="stDataFrame"]{border:1px solid #263850;border-radius:12px;overflow:hidden}
.upload-guide{background:linear-gradient(145deg,#17283e,#101c2d);border:1px solid #2a405b;border-radius:16px;padding:18px 20px;margin:8px 0 18px}
.result-card{background:linear-gradient(145deg,#17283e,#101c2d);border:1px solid #2a405b;border-radius:15px;padding:16px 18px;margin:7px 0}
.result-title{font-weight:700;color:#f3f8ff;font-size:16px}.result-meta{color:#91a4bc;font-size:12px;margin-top:5px}
.status{display:inline-block;border-radius:20px;padding:5px 10px;font-size:12px;font-weight:700}
@media(max-width:700px){.block-container{padding:1rem .8rem 2rem}h1{font-size:1.8rem!important}}
</style>
""", unsafe_allow_html=True)

st.title("📄 Predict Traffic from Your CSV")
st.caption("Upload a traffic data file and get a 15-minute traffic forecast for each observation.")

st.markdown("""
<div class="upload-guide">
<strong>How it works</strong><br>
1. Choose your traffic CSV file.<br>
2. We check the file and run the Kolkata-trained prediction model.<br>
3. View the results and download your prediction report.
</div>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Preparing the prediction model...")
def ensure_model():
    if not MODEL_PATH.is_file():
        # Train from the historical CSV included in the repository. No external API calls.
        from backend.prepare_model import main as prepare_model
        if not prepare_model():
            raise RuntimeError("The model could not be prepared because the historical training data is missing.")
    return load_model()

with st.expander("What columns should my CSV contain?", expanded=False):
    st.write("Your file must include the following columns:")
    st.code(", ".join(REQUIRED), language="text")
    st.write("Optional columns: latitude, longitude, time_zone.")
    st.caption("The timestamp must include a timezone (UTC is recommended). Maximum upload size: 25,000 data rows.")
    example = pd.DataFrame([{
        "timestamp_utc": "2026-10-18T10:00:00Z", "location_id": "Howrah Bridge",
        "current_speed_kmph": 24, "free_flow_speed_kmph": 45,
        "confidence": 0.92, "temperature_c": 30.5, "humidity_pct": 78,
        "rain_1h_mm": 0.0, "latitude": 22.5851, "longitude": 88.3468,
        "time_zone": "Asia/Kolkata"
    }])
    st.download_button("Download sample CSV template", example.to_csv(index=False),
                       "trafficiq_sample_template.csv", mime="text/csv")

uploaded_file = st.file_uploader("Choose your CSV file", type=["csv"], help="Upload a .csv file containing traffic and weather observations.")
if uploaded_file is None and st.session_state.get("use_default_historical_csv", False):
    historical = ROOT / "data/raw/kolkata_traffic_weather.csv"
    if historical.is_file():
        uploaded_file = historical
        st.info("Using the historical Kolkata dataset included with this project.")
    else:
        st.error("The included historical dataset could not be found.")
        st.stop()

if uploaded_file is None:
    st.info("Your results will appear here after you upload a CSV file.")
    st.stop()

try:
    with st.spinner("Checking your file and generating predictions..."):
        ensure_model()
        predictions, rejected = predict_csv(
            io.BytesIO(uploaded_file.getvalue()) if hasattr(uploaded_file, "getvalue") else uploaded_file
        )
except (ValueError, FileNotFoundError, RuntimeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f"We couldn't use this file: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Prediction could not be completed ({type(exc).__name__}). Please check the app logs.")
    st.stop()

if predictions.empty:
    st.error("No usable rows were found. Please check the required columns and upload the file again.")
    if not rejected.empty:
        with st.expander(f"See why {len(rejected)} row(s) were skipped"):
            st.dataframe(rejected[["source_row", "error"]], use_container_width=True, hide_index=True)
    st.stop()

st.success(f"Prediction complete — {len(predictions):,} row(s) processed.")
st.caption("Each prediction describes the expected traffic condition 15 minutes after that row's recorded time.")

valid_col, skipped_col, horizon_col = st.columns(3)
valid_col.metric("Rows predicted", f"{len(predictions):,}")
skipped_col.metric("Rows skipped", f"{len(rejected):,}")
horizon_col.metric("Forecast period", "15 minutes")

if not rejected.empty:
    with st.expander(f"Review {len(rejected):,} row(s) that were skipped"):
        st.caption("These rows had missing or invalid information. The remaining valid rows were still processed.")
        st.dataframe(rejected[["source_row", "error"]], use_container_width=True, hide_index=True)
        st.download_button("Download skipped rows report", rejected.to_csv(index=False),
                           "skipped_rows_report.csv", mime="text/csv")

roads = sorted(predictions["location_id"].astype(str).unique())
selected_roads = st.multiselect("Show selected locations", roads, default=roads)
shown = predictions[predictions["location_id"].astype(str).isin(selected_roads)].copy()

def friendly_status(value):
    label = str(value).strip().lower()
    if any(word in label for word in ("heavy", "high", "severe")):
        return "Heavy traffic", "#f54242"
    if any(word in label for word in ("moderate", "medium")):
        return "Moderate traffic", "#f5a142"
    if any(word in label for word in ("low", "light", "free")):
        return "Light traffic", "#34d47a"
    return str(value).replace("_", " ").title(), "#91a4bc"

st.markdown("### 📈 Traffic speed trend")
if not shown.empty and "current_speed_kmph" in shown.columns:
    chart_roads = sorted(shown["location_id"].astype(str).unique())
    chart_road = st.selectbox("Choose a location for the speed chart", chart_roads, key="csv_speed_chart_location")
    chart_data = shown[shown["location_id"].astype(str) == chart_road].copy()
    chart_data["timestamp_utc"] = pd.to_datetime(chart_data["timestamp_utc"], utc=True, errors="coerce")
    chart_data["current_speed_kmph"] = pd.to_numeric(chart_data["current_speed_kmph"], errors="coerce")
    chart_data = chart_data.dropna(subset=["timestamp_utc", "current_speed_kmph"]).sort_values("timestamp_utc")
    if len(chart_data) >= 2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_data["timestamp_utc"], y=chart_data["current_speed_kmph"],
            mode="lines+markers", name="Traffic speed",
            line=dict(width=3, color="#4da3ff"),
            fill="tozeroy", fillcolor="rgba(77,163,255,0.12)",
            hovertemplate="%{x|%d %b, %H:%M}<br>Speed: %{y:.1f} km/h<extra></extra>",
        ))
        if "free_flow_speed_kmph" in chart_data.columns:
            free_flow = pd.to_numeric(chart_data["free_flow_speed_kmph"], errors="coerce")
            if free_flow.notna().any():
                fig.add_trace(go.Scatter(
                    x=chart_data["timestamp_utc"], y=free_flow,
                    mode="lines", name="Usual free-flow speed",
                    line=dict(width=2, dash="dash", color="#34d47a"),
                    hovertemplate="Usual speed: %{y:.1f} km/h<extra></extra>",
                ))
        fig.update_layout(
            height=320, margin=dict(l=8, r=8, t=18, b=8),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a9bad0"), xaxis_title="Time",
            yaxis_title="Speed (km/h)", hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(145,164,188,0.15)", rangemode="tozero"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("A falling line means traffic is slowing down. The dashed line shows the usual free-flow speed when your CSV includes it.")
    else:
        st.info("At least two valid speed readings are needed to draw a trend for this location.")
else:
    st.info("This CSV does not contain usable current-speed readings, so a speed trend cannot be displayed.")

st.markdown("### 🚦 Your traffic forecast")
latest_by_road = shown.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
if latest_by_road.empty:
    st.info("No locations are selected. Choose one or more locations above.")
else:
    cards = st.columns(2)
    for index, (_, item) in enumerate(latest_by_road.iterrows()):
        label, color = friendly_status(item["predicted_congestion"])
        with cards[index % 2]:
            st.markdown(
                f'<div class="result-card"><div class="result-title">{str(item["location_id"])}</div>'
                f'<div style="margin-top:10px"><span class="status" style="background:{color}22;color:{color}">{label}</span></div>'
                f'<div class="result-meta">Recorded: {item["timestamp_utc"]}</div>'
                f'<div class="result-meta">Forecast for: {item["prediction_at_utc"]}</div></div>',
                unsafe_allow_html=True,
            )

st.download_button("⬇ Download all predictions", predictions.to_csv(index=False),
                   "kolkata_traffic_predictions.csv", mime="text/csv", use_container_width=True)

with st.expander("View the full prediction table"):
    display_columns = [
        column for column in (
            "location_id", "timestamp_utc", "prediction_at_utc",
            "predicted_congestion", "current_speed_kmph", "free_flow_speed_kmph",
        ) if column in shown.columns
    ]
    st.dataframe(shown[display_columns], use_container_width=True, hide_index=True)

# Show a map only when the uploaded file contains usable coordinates.
if {"latitude", "longitude"}.issubset(shown.columns):
    mapped = shown.dropna(subset=["latitude", "longitude"])
    mapped = mapped[mapped["latitude"].between(-90, 90) & mapped["longitude"].between(-180, 180)]
    if not mapped.empty:
        with st.expander("View predicted locations on a map", expanded=False):
            latest = mapped.sort_values("timestamp_utc").drop_duplicates("location_id", keep="last")
            map_view = folium.Map(
                location=[float(latest["latitude"].mean()), float(latest["longitude"].mean())],
                zoom_start=11, tiles=MAP_TILES,
            )
            colors = {"Low": "green", "Moderate": "orange", "Heavy": "red"}
            for _, row in latest.iterrows():
                label = str(row["predicted_congestion"])
                folium.CircleMarker(
                    location=[float(row["latitude"]), float(row["longitude"])],
                    radius=8, color=colors.get(label, "gray"), fill=True, fill_opacity=0.8,
                    tooltip=f"{row['location_id']}: {label}",
                ).add_to(map_view)
            if len(latest) > 1:
                map_view.fit_bounds(latest[["latitude", "longitude"]].values.tolist())
            st_folium(map_view, width=None, height=380, returned_objects=[])
            if OFFLINE_MODE:
                st.caption("Offline view: map markers are shown without online background tiles.")

st.caption("This tool uses the project's Python ML model. The model was trained with Kolkata data; results for other cities have not been locally validated.")
