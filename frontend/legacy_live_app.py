"""
TrafficIQ — Kolkata Traffic Congestion Prediction System (Streamlit frontend)

Data flow:  TomTom (traffic) + OpenWeather (weather)  ->  FastAPI backend  ->  ML model  ->  this dashboard

Rules this app follows (see the frontend guidelines):
  * Only data returned by the FastAPI backend is shown. No random, simulated or hardcoded
    traffic / weather / ML values. Missing data is shown as "Data unavailable".
  * No API keys live in this code; Render owns the external API credentials.
  * API failures show a clear message (data source / backend / ML model) and never crash the app.

Run (from the repo root):   cd frontend && pip install -r requirements.txt && streamlit run app.py
Streamlit Community Cloud uses the deployed FastAPI URL configured in BACKEND_URL.
"""
from __future__ import annotations

import html
import os
from datetime import datetime
from pathlib import Path

import folium
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from traffic_core import (
    IST,
    STATUS_STYLE,
    TRAFFIC_THRESHOLDS,
    UNAVAILABLE,
    BackendError,
    call_backend,
    classify_traffic,
    fmt_ts,
    format_confidence,
    haversine_km,
    load_history,
    location_mismatch,
    make_error,
    parse_current,
    parse_prediction,
    prediction_color,
    prediction_label,
    short_reason,
    speed_ratio,
)

# A hosted FastAPI server already owns ML inference and model training.
# Do not import joblib/scikit-learn or train on Streamlit when using Render.
try:
    _remote_backend = os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL", "")
except Exception:
    _remote_backend = os.getenv("BACKEND_URL", "")
if not str(_remote_backend).strip() or str(_remote_backend).strip().lower() == "local":
    st.error("Configure BACKEND_URL in Streamlit Cloud Secrets to your Render FastAPI URL.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION  (Task Fourteen — no secrets in code)
# Order of precedence: environment variable -> Streamlit secrets -> default.
# ══════════════════════════════════════════════════════════════════════════════
def get_setting(name, default=None):
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    try:
        return st.secrets[name]
    except Exception:  # no secrets file, or key not present
        return default


def as_bool(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


# Default is for local development only. In production set BACKEND_URL to the deployed backend.
BACKEND_URL = str(get_setting("BACKEND_URL", "")).strip().rstrip("/")
if BACKEND_URL != "local" and not BACKEND_URL.startswith(("http://", "https://")):
    st.error("BACKEND_URL must be a complete http(s) URL. Set it in Streamlit Community Cloud Secrets.")
    st.stop()
REQUEST_TIMEOUT = max(10.0, float(get_setting("REQUEST_TIMEOUT_SECONDS", 60)))
# Render free services may need time to wake from an idle/cold start.
HEALTH_TIMEOUT = max(60.0, float(get_setting("HEALTH_TIMEOUT_SECONDS", 60)))
HISTORICAL_CSV_PATH = str(get_setting("HISTORICAL_CSV_PATH", str(Path(__file__).resolve().parents[1] / "data/raw/kolkata_traffic_weather.csv")))
# If the backend cannot take a location yet, set SEND_LOCATION_TO_BACKEND=false to send
# no location (GET without params / POST with {}) so the backend uses its default Kolkata location.
SEND_LOCATION = as_bool(get_setting("SEND_LOCATION_TO_BACKEND", "true"))
CACHE_TTL_SECONDS = 60  # avoid hitting TomTom / OpenWeather (via the backend) on every widget click

HEALTH_PATH = "/health"
CURRENT_PATH = "/api/v1/data/current"
PREDICT_PATH = "/api/v1/predict"


# ══════════════════════════════════════════════════════════════════════════════
# KOLKATA LOCATIONS  (Task One — the single source for the place list, coordinates and route options)
#
# Coordinates are approximate landmark positions. They MUST still be verified, and the TomTom
# response for each point must be tested (a valid lat/lon does not guarantee TomTom has flow
# data for it). A location with no data is shown as "Data unavailable" — never filled in.
# Start with 3–5 locations; add more later (e.g. Sealdah 22.5686, 88.3708).
# ══════════════════════════════════════════════════════════════════════════════
KOLKATA_LOCATIONS = [
    {"name": "Esplanade", "lat": 22.5646, "lon": 88.3510},
    {"name": "Park Street", "lat": 22.5535, "lon": 88.3520},
    {"name": "Howrah Bridge", "lat": 22.5851, "lon": 88.3468},
    {"name": "EM Bypass", "lat": 22.5395, "lon": 88.3960},
    {"name": "Salt Lake", "lat": 22.5726, "lon": 88.4338},
]
KNOWN_PLACES = [loc["name"] for loc in KOLKATA_LOCATIONS]
PLACE_COORDS = {loc["name"]: (loc["lat"], loc["lon"]) for loc in KOLKATA_LOCATIONS}
KOLKATA_CENTER = (22.5726, 88.3639)

LAYER_LABELS = {
    "backend": "FastAPI backend",
    "data_source": "Data source (TomTom / OpenWeather, reported by the backend)",
    "ml_model": "ML model",
}

esc = html.escape


# ══════════════════════════════════════════════════════════════════════════════
# STYLE  (dark theme itself is set in .streamlit/config.toml)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#08111f; --panel:#111d2e; --panel2:#14243a; --line:#263850; --muted:#91a4bc; --blue:#4da3ff; --cyan:#42d6d0; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:radial-gradient(ellipse at 15% 0%,#142c49 0%,#08111f 42%,#070d18 100%); color:#edf5ff; }
[data-testid="stHeader"] { background:rgba(8,17,31,.72); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#101d30 0%,#0b1524 100%); border-right:1px solid #263850; }
[data-testid="stSidebar"] * { color:#dce9f8; }
.block-container { max-width:1500px; padding-top:2.1rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; color:#f3f8ff; }
h1 { font-size:2.35rem !important; font-weight:700 !important; }
h2 { font-size:1.55rem !important; } h3 { font-size:1.12rem !important; }
p, label, .stCaption { color:#a9bad0; }
.kpi { background:linear-gradient(145deg,#17283e 0%,#101c2d 100%); border:1px solid #2a405b; border-radius:18px; padding:18px 20px; min-height:118px; box-shadow:0 12px 30px rgba(0,0,0,.16); transition:transform .18s ease,border-color .18s ease; }
.kpi:hover { transform:translateY(-2px); border-color:#4da3ff; }
.kpi-label { font-size:11px; color:#8fa7c2; font-weight:700; text-transform:uppercase; letter-spacing:1.15px; }
.kpi-value { font-family:'Space Grotesk',sans-serif; font-weight:700; margin:9px 0 3px; line-height:1.15; word-break:break-word; }
.kpi-sub { font-size:11px; color:#8298b2; }
.pill { display:inline-block; padding:5px 11px; border-radius:99px; font-size:11px; font-weight:700; letter-spacing:.2px; border:1px solid currentColor; }
.field-label { font-size:10px; color:#8298b2; text-transform:uppercase; letter-spacing:1px; font-weight:700; }
.field-value { font-size:16px; font-weight:700; color:#edf5ff; margin-top:4px; }
.muted { color:#91a4bc; }
.stButton>button, .stDownloadButton>button { border-radius:10px; border:1px solid #3977b7; background:linear-gradient(110deg,#1768b4,#258fc4); color:white; font-weight:700; min-height:42px; transition:all .2s ease; }
.stButton>button:hover, .stDownloadButton>button:hover { border-color:#70c8ff; color:white; box-shadow:0 6px 20px #1768b455; }
div[data-testid="stMetric"] { background:linear-gradient(145deg,#17283e,#101c2d); border:1px solid #2a405b; padding:15px 17px; border-radius:15px; }
div[data-testid="stMetricLabel"] { color:#91a4bc; }
div[data-testid="stMetricValue"] { color:#f3f8ff; font-family:'Space Grotesk',sans-serif; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid #263850; }
.stTabs [data-baseweb="tab"] { background:#101d2e; border:1px solid #263850; border-radius:10px 10px 0 0; padding:10px 16px; color:#9fb2c9; }
.stTabs [aria-selected="true"] { background:#183452 !important; color:#73c5ff !important; border-color:#3977b7 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color:#263850 !important; border-radius:15px !important; background:rgba(17,29,46,.55); }
.stAlert { border-radius:12px; }
input, textarea, [data-baseweb="select"] > div { background:#101d2e !important; border-color:#314761 !important; }
hr { border-color:#263850 !important; }
[data-testid="stDataFrame"] { border:1px solid #263850; border-radius:12px; overflow:hidden; }
@media(max-width:700px) { .block-container{padding:1rem .8rem 2rem;} h1{font-size:1.8rem !important;} .kpi{padding:14px;min-height:100px;} }
</style>
""",
    unsafe_allow_html=True,
)


def pill(text, color):
    return f'<span class="pill" style="background:{color}26;color:{color}">{esc(str(text))}</span>'


def kpi_card(label, value, sub="", color=None):
    unavailable = value == UNAVAILABLE
    value_color = "#7b82a0" if unavailable else (color or "#eef0f6")
    value_size = "16px" if unavailable else "24px"
    sub_html = esc(sub) if sub else "&nbsp;"
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value" style="color:{value_color};font-size:{value_size}">{esc(str(value))}</div>'
        f'<div class="kpi-sub">{sub_html}</div></div>',
        unsafe_allow_html=True,
    )


def labeled(column, label, value, color=None):
    style = f' style="color:{color}"' if color else ""
    column.markdown(
        f'<div class="field-label">{esc(label)}</div><div class="field-value"{style}>{esc(str(value))}</div>',
        unsafe_allow_html=True,
    )


def fmt_speed(value):
    return f"{value:.0f} km/h" if value is not None else UNAVAILABLE


# ══════════════════════════════════════════════════════════════════════════════
# API LAYER  (Task Four — one clean calling function, timeouts, HTTP + JSON validation)
# Successful responses are cached briefly. Failures raise BackendError, which
# st.cache_data never caches, so a recovered backend works on the next refresh.
# ══════════════════════════════════════════════════════════════════════════════
def location_params(loc):
    return {"latitude": loc["lat"], "longitude": loc["lon"]} if SEND_LOCATION else None


def location_payload(loc):
    if not SEND_LOCATION:
        return {}  # default Kolkata location
    return {"location": loc["name"], "latitude": loc["lat"], "longitude": loc["lon"]}


@st.cache_data(ttl=15, show_spinner=False)
def _cached_health(base_url):
    result = call_backend(base_url, "GET", HEALTH_PATH, timeout=HEALTH_TIMEOUT)
    if not result["ok"]:
        raise BackendError(result["error"])
    return result


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _cached_current(base_url, lat, lon, send_location):
    params = {"latitude": lat, "longitude": lon} if send_location else None
    result = call_backend(base_url, "GET", CURRENT_PATH, params=params, timeout=REQUEST_TIMEOUT)
    if not result["ok"]:
        raise BackendError(result["error"])
    parsed = parse_current(result["data"])
    if not parsed["has_any_field"]:
        raise BackendError(make_error(
            "schema", "backend",
            f"The response from {CURRENT_PATH} contained none of the expected traffic or weather fields.",
            detail="Check the response format with the backend team (see 'Raw backend responses' in the Pipeline tab)."))
    return {"ok": True, "parsed": parsed, "raw": result["data"], "fetched_at": result["fetched_at"]}


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _cached_predict(base_url, payload_items):
    payload = dict(payload_items)
    result = call_backend(base_url, "POST", PREDICT_PATH, json_body=payload, timeout=REQUEST_TIMEOUT)
    if not result["ok"]:
        raise BackendError(result["error"])
    if not isinstance(result["data"], dict):
        raise BackendError(make_error(
            "schema", "backend", f"The response from {PREDICT_PATH} was not a JSON object."))
    parsed = parse_prediction(result["data"])
    if prediction_label(parsed["prediction"]) is None:
        reason = parsed["error"] if isinstance(parsed["error"], str) else None
        raise BackendError(make_error(
            "model", "ml_model",
            "The backend responded, but the response contains no prediction. The ML model may be "
            "unavailable or failed to load.",
            detail=reason))
    return {"ok": True, "parsed": parsed, "raw": result["data"], "fetched_at": result["fetched_at"]}


def _safe(function, *args):
    try:
        return function(*args)
    except BackendError as exc:
        return {"ok": False, "error": exc.error}


def get_health():
    return _safe(_cached_health, BACKEND_URL)


def get_current(loc):
    return _safe(_cached_current, BACKEND_URL, loc["lat"], loc["lon"], SEND_LOCATION)


def get_prediction(loc):
    payload = location_payload(loc)
    return _safe(_cached_predict, BACKEND_URL, tuple(sorted(payload.items())))


@st.cache_data(ttl=60, show_spinner=False)
def _cached_offline_predict(base_url):
    path = "/api/v1/predict/offline"
    result = call_backend(
        base_url,
        "GET",
        path,
        timeout=REQUEST_TIMEOUT,
    )

    if not result["ok"]:
        raise BackendError(result["error"])

    if not isinstance(result["data"], dict):
        raise BackendError(
            make_error("schema", "backend", "Offline prediction response is not a JSON object.")
        )

    parsed = parse_prediction(result["data"])

    if prediction_label(parsed["prediction"]) is None:
        raise BackendError(
            make_error("model", "ml_model", "Offline prediction is unavailable.")
        )

    return {
        "ok": True,
        "parsed": parsed,
        "raw": result["data"],
        "fetched_at": result["fetched_at"],
    }


def get_offline_prediction():
    return _safe(_cached_offline_predict, BACKEND_URL)

def load_all_current():
    """Fetch current data for every location; stop early if the backend itself is unreachable."""
    results, blocked = {}, None
    for loc in KOLKATA_LOCATIONS:
        if blocked:
            results[loc["name"]] = blocked
            continue
        result = get_current(loc)
        results[loc["name"]] = result
        if not result["ok"] and result["error"]["kind"] in ("connection", "timeout"):
            blocked = result
    return results


# ══════════════════════════════════════════════════════════════════════════════
# SIMPLE, USER-FRIENDLY KOLKATA DASHBOARD
# Technical diagnostics stay in the backend/logs, not on the public dashboard.
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("সহজে জানুন কলকাতার রাস্তায় এখন কী অবস্থা")
    selected_name = st.selectbox("কোন এলাকার খবর দেখতে চান?", KNOWN_PLACES, index=0)
    selected = next(loc for loc in KOLKATA_LOCATIONS if loc["name"] == selected_name)
    if st.button("🔄 নতুন তথ্য দেখুন", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("🚦 Kolkata Traffic Update")
st.caption(f"এখনকার যানজট এবং আগামী ১৫ মিনিটের সম্ভাব্য অবস্থা · {selected_name}")

with st.spinner("রাস্তার সর্বশেষ তথ্য আনা হচ্ছে…"):
    health = get_health()
    if health["ok"]:
        current = get_current(selected)
        prediction_result = get_prediction(selected)
    else:
        current = {"ok": False, "error": health["error"]}
        prediction_result = {"ok": False, "error": health["error"]}

info = current["parsed"] if current["ok"] else None
traffic = info["traffic"] if info else {"current_speed": None, "free_flow_speed": None,
                                         "current_travel_time": None, "free_flow_travel_time": None}
weather = info["weather"] if info else {"temperature": None, "humidity": None, "condition": None,
                                         "rainfall": None, "wind_speed": None}
status_key = classify_traffic(traffic["current_speed"], traffic["free_flow_speed"])
status = STATUS_STYLE[status_key]
pred = prediction_result["parsed"] if prediction_result["ok"] else None
pred_label = prediction_label(pred["prediction"]) if pred else None
collected_at = info["collected_at"] if info else None
if collected_at is None and pred:
    collected_at = pred["collected_at"]

def friendly_traffic_label(value):
    if not value:
        return "তথ্য পাওয়া যায়নি"
    normalized = str(value).strip().lower()
    if "heavy" in normalized or "high" in normalized:
        return "প্রচণ্ড যানজট"
    if "moderate" in normalized or "medium" in normalized:
        return "মাঝারি যানজট"
    if "low" in normalized or "light" in normalized or "free" in normalized:
        return "কম যানজট"
    return str(value)

def friendly_current_status(key):
    return {
        "Heavy": "প্রচণ্ড যানজট",
        "Moderate": "মাঝারি যানজট",
        "Low": "রাস্তা বেশ ফাঁকা",
        None: "তথ্য পাওয়া যায়নি",
    }[key]

if not current["ok"]:
    st.warning("এই মুহূর্তে রাস্তার তথ্য পাওয়া যাচ্ছে না। কিছুক্ষণ পরে আবার চেষ্টা করুন।")
elif info and location_mismatch(selected_name, info["reported_location"]):
    st.info("এই এলাকার আলাদা তথ্য এখন পাওয়া যায়নি। নিচের তথ্যটি অন্য একটি এলাকার হতে পারে।")

# Main information: current conditions and the model's 15-minute forecast.
now_col, forecast_col = st.columns(2, gap="large")
with now_col:
    st.markdown("### 🚗 এখনকার যানজট")
    now_label = friendly_current_status(status_key)
    now_color = status["color"]
    st.markdown(
        f'<div class="kpi" style="min-height:150px">'
        f'<div class="kpi-label">এই মুহূর্তের রাস্তার অবস্থা</div>'
        f'<div class="kpi-value" style="font-size:27px;color:{now_color}">{esc(now_label)}</div>'
        f'<div class="kpi-sub">{esc(selected_name)}</div></div>',
        unsafe_allow_html=True,
    )
    if traffic["current_speed"] is not None:
        st.metric("গাড়ি চলছে গড়ে", f"{traffic['current_speed']:.0f} কিমি/ঘণ্টা")
    else:
        st.caption("গাড়ির গতির তথ্য পাওয়া যায়নি।")

with forecast_col:
    st.markdown("### 🔮 ১৫ মিনিট পরের পূর্বাভাস")
    if pred_label:
        forecast_label = friendly_traffic_label(pred_label)
        forecast_color = prediction_color(pred_label) or "#91a4bc"
        st.markdown(
            f'<div class="kpi" style="min-height:150px">'
            f'<div class="kpi-label">আমাদের মডেলের অনুমান</div>'
            f'<div class="kpi-value" style="font-size:27px;color:{forecast_color}">{esc(forecast_label)}</div>'
            f'<div class="kpi-sub">{esc(selected_name)} · আগামী ১৫ মিনিট</div></div>',
            unsafe_allow_html=True,
        )
        if "প্রচণ্ড" in forecast_label:
            st.warning("আগামী ১৫ মিনিটে যানজট বাড়তে পারে। যাত্রার আগে আবার দেখে নিন।")
        elif "মাঝারি" in forecast_label:
            st.info("কিছুটা ধীরগতির যান চলাচল হতে পারে।")
        elif "কম যানজট" in forecast_label:
            st.success("যান চলাচল স্বাভাবিক থাকার সম্ভাবনা বেশি।")
    else:
        st.markdown(
            '<div class="kpi" style="min-height:150px">'
            '<div class="kpi-label">আগামী ১৫ মিনিট</div>'
            '<div class="kpi-value" style="font-size:22px;color:#91a4bc">পূর্বাভাস পাওয়া যায়নি</div>'
            '<div class="kpi-sub">পরে আবার চেষ্টা করুন</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("### 🌤️ আজকের আবহাওয়া")
weather_cols = st.columns(3)
weather_items = [
    ("তাপমাত্রা", f"{weather['temperature']:.0f}°C" if weather["temperature"] is not None else "পাওয়া যায়নি"),
    ("আবহাওয়া", weather["condition"].capitalize() if weather["condition"] else "পাওয়া যায়নি"),
    ("বৃষ্টিপাত", f"{weather['rainfall']:g} মিমি" if weather["rainfall"] is not None else "পাওয়া যায়নি"),
]
for column, (label, value) in zip(weather_cols, weather_items):
    with column:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value" style="font-size:21px">{esc(value)}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("### 📈 রাস্তার গতির পরিবর্তন")
history = load_history(HISTORICAL_CSV_PATH, selected_name)
if history["df"] is None:
    st.caption("এই এলাকার আগের গতির তথ্য এখনও পাওয়া যায়নি। তথ্য পাওয়া গেলে এখানে সহজ গ্রাফ দেখা যাবে।")
else:
    frame = history["df"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frame["time"], y=frame["speed"], mode="lines",
        name="গাড়ির গতি", line=dict(color="#4da3ff", width=3),
        fill="tozeroy", fillcolor="rgba(77,163,255,0.12)",
    ))
    fig.update_layout(
        height=250, margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#a9bad0"},
        xaxis_title="", yaxis_title="গতি (কিমি/ঘণ্টা)",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(145,164,188,0.15)", rangemode="tozero"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("গ্রাফে লাইন উপরে উঠলে গাড়ির গতি বাড়ছে, নিচে নামলে গতি কমছে।")

if collected_at:
    st.caption(f"সর্বশেষ তথ্য: {fmt_ts(collected_at)}")
st.caption("যানজটের পূর্বাভাস একটি অনুমান; রাস্তায় বের হওয়ার আগে আবার তথ্য দেখে নিন।")
