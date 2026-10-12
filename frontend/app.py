"""
TrafficIQ — Kolkata Traffic Congestion Prediction System (Streamlit frontend)

Data flow:  TomTom (traffic) + OpenWeather (weather)  ->  FastAPI backend  ->  ML model  ->  this dashboard

Rules this app follows (see the frontend guidelines):
  * Only data returned by the FastAPI backend is shown. No random, simulated or hardcoded
    traffic / weather / ML values. Missing data is shown as "Data unavailable".
  * No API keys live in this code. Local mode reads API keys from environment/Streamlit secrets.
  * API failures show a clear message (data source / backend / ML model) and never crash the app.

Run (from the repo root):   cd frontend && pip install -r requirements.txt && streamlit run app.py
Streamlit Community Cloud uses the deployed FastAPI URL configured in BACKEND_URL.
"""
from __future__ import annotations

import html
import os
import sys
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

# Prepare the trained model from the real historical CSV if the artifact is absent.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
@st.cache_resource(show_spinner="Preparing Kolkata ML model…")
def _prepare_local_model():
    from scripts.prepare_model import main as prepare
    # Streamlit secrets are not automatically exported as environment variables.
    for name in ("TOMTOM_API_KEY", "OPENWEATHER_API_KEY"):
        if not os.getenv(name):
            try:
                value = st.secrets.get(name)
                if value:
                    os.environ[name] = str(value)
            except Exception:
                pass
    # Settings are instantiated on first import; import only after secrets are loaded.
    prepare()
    return True
st.set_page_config(
    page_title="TrafficIQ — Kolkata",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
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
REQUEST_TIMEOUT = float(get_setting("REQUEST_TIMEOUT_SECONDS", 10))
HEALTH_TIMEOUT = 3.0
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
  .kpi{background:#171c27;border:1px solid #222838;border-radius:14px;padding:14px 16px;min-height:104px}
  .kpi-label{font-size:12px;color:#7b82a0;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
  .kpi-value{font-weight:700;margin:6px 0 2px;line-height:1.2;word-break:break-word}
  .kpi-sub{font-size:12px;color:#7b82a0}
  .pill{display:inline-block;padding:2px 10px;border-radius:6px;font-size:12px;font-weight:700}
  .field-label{font-size:11px;color:#7b82a0;text-transform:uppercase;letter-spacing:.4px}
  .field-value{font-size:16px;font-weight:600}
  .muted{color:#7b82a0}
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Kolkata traffic congestion prediction")
    st.divider()

    selected_name = st.selectbox("📍 Location", KNOWN_PLACES, index=0)
    selected = next(loc for loc in KOLKATA_LOCATIONS if loc["name"] == selected_name)

    # Task Twelve: refresh button that triggers real API requests again.
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()

    st.divider()
    st.markdown("**Backend**")
    st.caption(BACKEND_URL)
    health_slot = st.empty()
    st.divider()
    st.caption(
        "Traffic: TomTom API · Weather: OpenWeather API · both accessed only through the FastAPI backend. "
        "No API keys are stored in the frontend."
    )

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA  (Phase 3–6: current data, prediction, loading state)
# ══════════════════════════════════════════════════════════════════════════════
health = get_health()
if health["ok"]:
    health_slot.success("✅ Backend reachable")
else:
    health_error = health["error"]
    if health_error["kind"] in ("connection", "timeout"):
        health_slot.error("❌ Backend not reachable")
    else:
        health_slot.warning(f"⚠️ Health check failed ({health_error['message']})")

# If the backend cannot even be reached, skip the other calls instead of waiting on each one.
blocked = None
if not health["ok"] and health["error"]["kind"] in ("connection", "timeout"):
    blocked = health

with st.spinner("Fetching live data from the backend…"):
    if blocked:
        current_results = {loc["name"]: blocked for loc in KOLKATA_LOCATIONS}
        prediction_result = blocked
    else:
        current_results = load_all_current()
        prediction_result = get_prediction(selected)

fetched_now = datetime.now(IST).strftime("%d %b %Y, %H:%M:%S IST")
with st.sidebar:
    st.caption(f"Last refresh: {fetched_now}")

current = current_results[selected_name]
info = current["parsed"] if current["ok"] else None
traffic = info["traffic"] if info else {"current_speed": None, "free_flow_speed": None,
                                         "current_travel_time": None, "free_flow_travel_time": None}
weather = info["weather"] if info else {"temperature": None, "humidity": None, "condition": None,
                                         "rainfall": None, "wind_speed": None}
status_key = classify_traffic(traffic["current_speed"], traffic["free_flow_speed"])
status = STATUS_STYLE[status_key]
pred = prediction_result["parsed"] if prediction_result["ok"] else None
pred_label = prediction_label(pred["prediction"]) if pred else None


# ══════════════════════════════════════════════════════════════════════════════
# HEADER + ERROR SUMMARY + KPI CARDS  (Task Six)
# ══════════════════════════════════════════════════════════════════════════════
st.title("🚦 TrafficIQ — Kolkata")
st.caption(f"Live traffic and weather via the FastAPI backend · showing **{selected_name}**")


def show_error(title, error):
    layer = LAYER_LABELS.get(error["layer"], "FastAPI backend")
    inferred = " (inferred from the error text)" if error["kind"] == "http" else ""
    st.error(f"**{title}** — where it failed: {layer}{inferred}. {error['message']}")
    if error.get("detail"):
        st.caption(f"Details: {error['detail']}")


# Show each distinct problem once instead of once per location.
seen = set()
for result in current_results.values():
    if not result["ok"]:
        key = (result["error"]["kind"], result["error"]["message"], result["error"].get("detail"))
        if key not in seen:
            seen.add(key)
            show_error("Live traffic / weather data unavailable", result["error"])
if not prediction_result["ok"]:
    error = prediction_result["error"]
    key = (error["kind"], error["message"], error.get("detail"))
    if key not in seen:
        title = "Model unavailable" if error["layer"] == "ml_model" else "Prediction unavailable"
        show_error(title, error)

# Real traffic never gives identical numbers and timestamps for several different places. If it does,
# the backend is most likely ignoring the location and returning its default location every time.
_fingerprints = {
    (r["parsed"]["traffic"]["current_speed"], r["parsed"]["traffic"]["free_flow_speed"], r["parsed"]["collected_at"])
    for r in current_results.values() if r["ok"]
}
_ok_count = sum(1 for r in current_results.values() if r["ok"])
if _ok_count >= 2 and len(_fingerprints) == 1:
    st.warning(
        "Every location returned **identical** traffic data. The backend may be ignoring the requested "
        "location and always answering for its default location, so the per-location values in the "
        "Roads and Map tabs should not be treated as separate readings. Confirm with the backend team "
        "how to request a specific location (see the README)."
    )

if current["ok"] and location_mismatch(selected_name, info["reported_location"]):
    st.warning(
        f"The backend reports this data is for **{info['reported_location']}**, not **{selected_name}**. "
        "The backend may not support per-location queries yet — treat the numbers below as belonging "
        "to the location the backend reports."
    )

collected_at = info["collected_at"] if info else None
if collected_at is None and pred:
    collected_at = pred["collected_at"]

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Current Speed", fmt_speed(traffic["current_speed"]),
             f"Free-flow: {fmt_speed(traffic['free_flow_speed'])}" if traffic["free_flow_speed"] is not None else "")
with k2:
    kpi_card("Traffic Status", status["label"] if status_key else UNAVAILABLE,
             "Current vs free-flow speed" if status_key else "", color=status["color"])
with k3:
    temp = weather["temperature"]
    cond = weather["condition"]
    weather_value = f"{temp:.0f}°C" if temp is not None else (cond.capitalize() if cond else UNAVAILABLE)
    kpi_card("Weather", weather_value, cond.capitalize() if (cond and temp is not None) else "")
with k4:
    kpi_card("Last Updated", fmt_ts(collected_at), "collected_at from backend" if collected_at else "")

st.write("")
tab_overview, tab_roads, tab_map, tab_route, tab_pipeline = st.tabs(
    ["📊 Overview", "🛣️ Roads", "🗺️ Map", "🧪 Route (demo)", "⚙️ Pipeline"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW  (Task Five + Task Seven)
# ══════════════════════════════════════════════════════════════════════════════
def render_prediction_card():
    st.markdown("#### 🤖 ML prediction")
    with st.container(border=True):
        if not prediction_result["ok"]:
            error = prediction_result["error"]
            if error["layer"] == "ml_model":
                st.markdown(pill("Model unavailable", "#7b82a0"), unsafe_allow_html=True)
            else:
                st.markdown(pill("Prediction unavailable", "#7b82a0"), unsafe_allow_html=True)
            st.caption(f"{short_reason(error).capitalize()} — see the message at the top of the page.")
            return
        color = prediction_color(pred_label)
        st.markdown(
            f'<div class="field-label">Predicted congestion level</div>'
            f'<div style="font-size:26px;font-weight:700;color:{color}">{esc(pred_label)}</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        labeled(c1, "Location", selected_name)
        confidence = format_confidence(pred["confidence"])
        labeled(c2, "Confidence", confidence if confidence else "Not provided by the model")
        c3, c4 = st.columns(2)
        labeled(c3, "Prediction time", fmt_ts(pred["collected_at"]))
        labeled(c4, "Data source", str(pred["source"]) if pred["source"] else UNAVAILABLE)
        if isinstance(pred["location"], str) and location_mismatch(selected_name, pred["location"]):
            st.caption(f"⚠️ Backend-reported location for this prediction: {pred['location']}")


def build_recommendation():
    """Recommendation built only from real API / model values — no hardcoded delays or clearing times."""
    if status_key is None:
        return None
    lines = [f"Current speed at **{selected_name}** is **{traffic['current_speed']:.0f} km/h** "
             f"against a free-flow speed of **{traffic['free_flow_speed']:.0f} km/h**."]
    if status_key == "Heavy":
        lines.append("Heavy congestion — consider delaying the trip or choosing another route.")
    elif status_key == "Moderate":
        lines.append("Moderate congestion — allow extra travel time.")
    else:
        lines.append("Traffic is flowing close to free-flow speed.")
    cur_t, free_t = traffic["current_travel_time"], traffic["free_flow_travel_time"]
    if cur_t is not None and free_t is not None and cur_t > free_t:
        lines.append(f"Extra delay on this road segment (TomTom travel times): **{(cur_t - free_t) / 60:.1f} min**.")
    if pred_label:
        lines.append(f"ML model prediction: **{esc(pred_label)}**.")
    return "  \n".join(lines)


with tab_overview:
    # Alerts only when a verified condition exists.
    if status_key == "Heavy":
        st.warning(f"⚠️ High congestion at **{selected_name}** based on live TomTom speed data.")
    if pred_label and prediction_color(pred_label) == "#f54242":
        st.warning(f"⚠️ The ML model predicts **{esc(pred_label)}** for **{selected_name}**.")

    recommendation = build_recommendation()
    if recommendation:
        st.info("💡 **What you should do**  \n" + recommendation)
    else:
        st.info("💡 Recommendation unavailable — live speed data is not available for this location.")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Speed vs free-flow")
        ratio = speed_ratio(traffic["current_speed"], traffic["free_flow_speed"])
        if ratio is None:
            st.info(UNAVAILABLE + " — needs both current and free-flow speed from the API.")
        else:
            pct = max(0.0, min(ratio * 100, 100.0))
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%", "valueformat": ".0f", "font": {"size": 40}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": status["color"], "thickness": 0.28},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, TRAFFIC_THRESHOLDS["moderate"] * 100], "color": "rgba(245,66,66,.18)"},
                        {"range": [TRAFFIC_THRESHOLDS["moderate"] * 100, TRAFFIC_THRESHOLDS["low"] * 100],
                         "color": "rgba(245,133,66,.18)"},
                        {"range": [TRAFFIC_THRESHOLDS["low"] * 100, 100], "color": "rgba(52,212,122,.18)"},
                    ],
                },
            ))
            gauge.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=10),
                                paper_bgcolor="rgba(0,0,0,0)", font={"color": "#eef0f6"})
            st.plotly_chart(gauge, use_container_width=True)
            st.caption(f"{traffic['current_speed']:.0f} km/h now vs {traffic['free_flow_speed']:.0f} km/h free-flow "
                       f"→ **{status['label']}** (Low ≥ {TRAFFIC_THRESHOLDS['low']:.0%}, "
                       f"Moderate ≥ {TRAFFIC_THRESHOLDS['moderate']:.0%} of free-flow; provisional thresholds).")

    with right:
        render_prediction_card()

    st.markdown("#### 🌤 Weather (OpenWeather via backend)")
    w1, w2, w3, w4, w5 = st.columns(5)
    labeled(w1, "Temperature", f"{weather['temperature']:.0f} °C" if weather["temperature"] is not None else UNAVAILABLE)
    labeled(w2, "Humidity", f"{weather['humidity']:.0f}%" if weather["humidity"] is not None else UNAVAILABLE)
    labeled(w3, "Condition", weather["condition"].capitalize() if weather["condition"] else UNAVAILABLE)
    labeled(w4, "Rainfall", f"{weather['rainfall']:g} mm" if weather["rainfall"] is not None else UNAVAILABLE)
    labeled(w5, "Wind speed", f"{weather['wind_speed']:g}" if weather["wind_speed"] is not None else UNAVAILABLE)
    st.caption("Weather values are shown exactly as returned by the backend. Wind speed has no unit conversion "
               "(OpenWeather returns m/s when the backend requests metric units).")

    st.markdown("#### Speed trend (historical CSV)")
    history = load_history(HISTORICAL_CSV_PATH, selected_name)
    if history["df"] is None:
        st.info(history["message"])
        st.caption(f"Looked for the CSV at: `{HISTORICAL_CSV_PATH}` (set HISTORICAL_CSV_PATH to change).")
    else:
        frame = history["df"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=frame["time"], y=frame["speed"], mode="lines", name="Speed",
                                 line=dict(color="#4e9fff", width=2.5)))
        if history["has_free_flow"]:
            fig.add_trace(go.Scatter(x=frame["time"], y=frame["free_flow"], mode="lines", name="Free-flow",
                                     line=dict(color="#7b82a0", width=1.5, dash="dash")))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font={"color": "#eef0f6"}, yaxis_title="km/h", legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
        if history["note"]:
            st.caption(history["note"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ROADS  (Task Eight)
# ══════════════════════════════════════════════════════════════════════════════
with tab_roads:
    st.markdown("#### Traffic status — selected Kolkata locations")
    plot_rows = []
    for loc in KOLKATA_LOCATIONS:
        result = current_results[loc["name"]]
        with st.container(border=True):
            if not result["ok"]:
                st.markdown(f"**{esc(loc['name'])}** &nbsp; {pill(UNAVAILABLE, '#7b82a0')}", unsafe_allow_html=True)
                st.caption(f"Reason: {short_reason(result['error'])}")
                continue
            row = result["parsed"]
            row_traffic = row["traffic"]
            row_key = classify_traffic(row_traffic["current_speed"], row_traffic["free_flow_speed"])
            row_status = STATUS_STYLE[row_key]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
            c1.markdown(f"**{esc(loc['name'])}**<br>{pill(row_status['label'], row_status['color'])}",
                        unsafe_allow_html=True)
            labeled(c2, "Current speed", fmt_speed(row_traffic["current_speed"]), row_status["color"])
            labeled(c3, "Free-flow speed", fmt_speed(row_traffic["free_flow_speed"]))
            labeled(c4, "Last updated", fmt_ts(row["collected_at"]))
            if location_mismatch(loc["name"], row["reported_location"]):
                st.caption(f"⚠️ Backend reports this data for: {row['reported_location']}")
            if row_traffic["current_speed"] is not None and row_traffic["free_flow_speed"] is not None:
                plot_rows.append((loc["name"], row_traffic["current_speed"], row_traffic["free_flow_speed"]))

    if plot_rows:
        bars = go.Figure()
        bars.add_trace(go.Bar(name="Current speed", x=[r[0] for r in plot_rows], y=[r[1] for r in plot_rows],
                              marker_color="#4e9fff"))
        bars.add_trace(go.Bar(name="Free-flow speed", x=[r[0] for r in plot_rows], y=[r[2] for r in plot_rows],
                              marker_color="#7b82a0"))
        bars.update_layout(barmode="group", height=300, margin=dict(l=10, r=10, t=10, b=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font={"color": "#eef0f6"}, yaxis_title="km/h", legend=dict(orientation="h"))
        st.plotly_chart(bars, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MAP  (Task Nine) — Kolkata markers coloured by the API-derived traffic status
# ══════════════════════════════════════════════════════════════════════════════
with tab_map:
    st.markdown("#### Kolkata — traffic status by location")
    kolkata_map = folium.Map(location=KOLKATA_CENTER, zoom_start=12, tiles="CartoDB dark_matter",
                             control_scale=True)
    for loc in KOLKATA_LOCATIONS:
        result = current_results[loc["name"]]
        if result["ok"]:
            row_traffic = result["parsed"]["traffic"]
            row_key = classify_traffic(row_traffic["current_speed"], row_traffic["free_flow_speed"])
            row_status = STATUS_STYLE[row_key]
            body = (f"<b>{esc(loc['name'])}</b><br>{esc(row_status['label'])}<br>"
                    f"Current: {esc(fmt_speed(row_traffic['current_speed']))}<br>"
                    f"Free-flow: {esc(fmt_speed(row_traffic['free_flow_speed']))}")
        else:
            row_status = STATUS_STYLE[None]
            body = f"<b>{esc(loc['name'])}</b><br>{UNAVAILABLE}"  # no speed is invented
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=12, color=row_status["color"], weight=3,
            fill=True, fill_color=row_status["color"], fill_opacity=0.65,
            tooltip=f"{loc['name']} — {row_status['label']}",
            popup=folium.Popup(body, max_width=240),
        ).add_to(kolkata_map)

    legend = "".join(
        f'<span style="color:{style["color"]}">●</span> {esc(style["label"])}<br>'
        for style in (STATUS_STYLE["Low"], STATUS_STYLE["Moderate"], STATUS_STYLE["Heavy"], STATUS_STYLE[None])
    )
    kolkata_map.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:24px;left:24px;background:#1e2435;border:1px solid #222838;'
        'border-radius:10px;padding:10px 14px;font-size:12px;color:#eef0f6;z-index:1000">'
        f"{legend}</div>"))
    # returned_objects=[] stops map clicks from re-running the script (and re-calling the APIs)
    st_folium(kolkata_map, height=480, use_container_width=True, returned_objects=[], key="kolkata_map")
    st.caption("Marker colour is the traffic status from live API speeds. Grey = data unavailable for that location.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ROUTE (DEMO)  (Task Ten)
# ══════════════════════════════════════════════════════════════════════════════
with tab_route:
    st.warning(
        "🧪 **Demo.** Distances here are **straight-line** estimates between two points — not road routes. "
        "No travel time or ETA is shown: real routes, distances and ETAs need the TomTom Routing API, "
        "which has not been integrated yet."
    )
    r1, r2 = st.columns(2)
    from_place = r1.selectbox("🟢 Starting point", KNOWN_PLACES, index=0, key="route_from")
    to_place = r2.selectbox("🔴 Destination", KNOWN_PLACES, index=min(2, len(KNOWN_PLACES) - 1), key="route_to")

    if from_place == to_place:
        st.info("Choose two different locations.")
    else:
        (lat1, lon1), (lat2, lon2) = PLACE_COORDS[from_place], PLACE_COORDS[to_place]
        m1, m2, m3 = st.columns(3)
        m1.metric("Straight-line distance", f"{haversine_km(lat1, lon1, lat2, lon2):.1f} km",
                  help="Great-circle distance, not the road distance.")
        for column, name in ((m2, from_place), (m3, to_place)):
            result = current_results[name]
            if result["ok"]:
                t = result["parsed"]["traffic"]
                label = STATUS_STYLE[classify_traffic(t["current_speed"], t["free_flow_speed"])]["label"]
            else:
                label = UNAVAILABLE
            column.metric(f"Traffic at {name}", label)

        route_map = folium.Map(location=[(lat1 + lat2) / 2, (lon1 + lon2) / 2], zoom_start=12,
                               tiles="CartoDB dark_matter")
        folium.PolyLine([[lat1, lon1], [lat2, lon2]], color="#4e9fff", weight=4, opacity=0.8,
                        dash_array="10 8", tooltip="Straight line (not a road route)").add_to(route_map)
        folium.Marker([lat1, lon1], tooltip=f"From: {from_place}", icon=folium.Icon(color="green")).add_to(route_map)
        folium.Marker([lat2, lon2], tooltip=f"To: {to_place}", icon=folium.Icon(color="red")).add_to(route_map)
        st_folium(route_map, height=380, use_container_width=True, returned_objects=[], key="route_map")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — PIPELINE  (Task Eleven) — each step reflects what was actually observed
# ══════════════════════════════════════════════════════════════════════════════
def step_status(kind, text):
    icons = {"ok": ("✅", "#34d47a"), "error": ("❌", "#f54242"), "unknown": ("⚪", "#7b82a0")}
    return icons[kind] + (text,)


def pipeline_steps():
    steps = []
    # 1 + 2: traffic and weather, judged from the selected location's current-data response
    if current["ok"]:
        has_traffic = traffic["current_speed"] is not None and traffic["free_flow_speed"] is not None
        has_weather = any(v is not None for v in weather.values())
        steps.append(("1. Traffic data collection", "TomTom API",
                      step_status("ok", "Data received") if has_traffic
                      else step_status("error", "No traffic fields in the response")))
        steps.append(("2. Weather data collection", "OpenWeather API",
                      step_status("ok", "Data received") if has_weather
                      else step_status("error", "No weather fields in the response")))
    else:
        reason = short_reason(current["error"])
        steps.append(("1. Traffic data collection", "TomTom API", step_status("unknown", f"Unavailable: {reason}")))
        steps.append(("2. Weather data collection", "OpenWeather API", step_status("unknown", f"Unavailable: {reason}")))
    # 3: feature engineering happens inside the backend and is not directly observable here
    steps.append(("3. Feature engineering", "Backend",
                  step_status("ok", "Completed (inferred from a successful prediction)") if prediction_result["ok"]
                  else step_status("unknown", "Cannot be confirmed — no successful prediction")))
    # 4: ML inference
    if prediction_result["ok"]:
        steps.append(("4. ML inference", "Python model", step_status("ok", "Model returned a prediction")))
    else:
        error = prediction_result["error"]
        text = "Model unavailable" if error["layer"] == "ml_model" else "Not reached — " + short_reason(error)
        steps.append(("4. ML inference", "Python model", step_status("error" if error["layer"] == "ml_model" else "unknown", text)))
    # 5: prediction response
    if prediction_result["ok"]:
        steps.append(("5. Prediction response", "FastAPI", step_status("ok", "Responding")))
    elif health["ok"]:
        steps.append(("5. Prediction response", "FastAPI",
                      step_status("error", "Backend is up, but the prediction endpoint failed")))
    else:
        steps.append(("5. Prediction response", "FastAPI", step_status("error", "Backend unreachable")))
    steps.append(("6. Dashboard rendering", "Streamlit", step_status("ok", "Running")))
    return steps


with tab_pipeline:
    st.markdown("#### Actual workflow status")
    st.caption("Status is based on what the backend actually returned in this refresh. "
               "A passing health check does not mean ML predictions work — the prediction endpoint is checked separately.")
    for name, provider, (icon, color, text) in pipeline_steps():
        with st.container(border=True):
            c1, c2 = st.columns([2, 5])
            c1.markdown(f"**{esc(name)}**<br><span class='muted'>{esc(provider)}</span>", unsafe_allow_html=True)
            c2.markdown(f'<span style="color:{color};font-weight:600">{icon} {esc(text)}</span>', unsafe_allow_html=True)

    st.markdown("#### Model performance")
    st.info("Accuracy, precision, recall and F1 will be shown here once the ML team provides verified results.")

    with st.expander("Raw backend responses (for verifying field names with the backend team)"):
        st.caption(f"GET {CURRENT_PATH} for {selected_name}")
        st.json(current["raw"] if current["ok"] else current["error"])
        st.caption(f"POST {PREDICT_PATH} for {selected_name}")
        st.json(prediction_result["raw"] if prediction_result["ok"] else prediction_result["error"])

st.divider()
st.caption(f"TrafficIQ · Kolkata · backend: {BACKEND_URL} · last refresh {fetched_now}")
