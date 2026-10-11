"""
traffic_core.py — logic for the TrafficIQ frontend that does not depend on Streamlit.

Everything here works with data returned by the FastAPI backend. Nothing in this
module generates, guesses or falls back to made-up traffic, weather or ML values:
if a value is missing, the functions return None and the UI shows "Data unavailable".

Kept separate from app.py so it can be unit-tested without running Streamlit.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

UNAVAILABLE = "Data unavailable"
HISTORY_UNAVAILABLE = "Historical data is not yet available for this location."

# India has no daylight saving, so a fixed offset is enough (no tzdata package needed).
IST = timezone(timedelta(hours=5, minutes=30))


# ══════════════════════════════════════════════════════════════════════════════
# TRAFFIC STATUS CLASSIFICATION  (Task Two / Task Eight)
# One function, used by the Overview, Roads, Map and Route tabs, so the tabs can
# never contradict each other.
#
# PROVISIONAL THRESHOLDS — to be confirmed with the ML and backend teams.
# ratio = current speed / free-flow speed (both from the TomTom data via the backend)
# ══════════════════════════════════════════════════════════════════════════════
TRAFFIC_THRESHOLDS = {"low": 0.90, "moderate": 0.70}

STATUS_STYLE = {
    "Low": {"label": "Low congestion", "color": "#34d47a"},
    "Moderate": {"label": "Moderate congestion", "color": "#f58542"},
    "Heavy": {"label": "Heavy congestion", "color": "#f54242"},
    None: {"label": UNAVAILABLE, "color": "#7b82a0"},
}


def speed_ratio(current_speed, free_flow_speed):
    if current_speed is None or free_flow_speed is None or free_flow_speed <= 0:
        return None
    return current_speed / free_flow_speed


def classify_traffic(current_speed, free_flow_speed, thresholds=None):
    """Return "Low", "Moderate", "Heavy" or None (when the API did not give both speeds)."""
    thresholds = thresholds or TRAFFIC_THRESHOLDS
    ratio = speed_ratio(current_speed, free_flow_speed)
    if ratio is None:
        return None
    if ratio >= thresholds["low"]:
        return "Low"
    if ratio >= thresholds["moderate"]:
        return "Moderate"
    return "Heavy"


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND ERRORS  (Task Twelve)
# Errors are plain dicts so they can safely pass through st.cache_data.
#   kind : connection | timeout | request | http | invalid_json | schema | model
#   layer: backend | data_source | ml_model   (so users can tell where it failed)
# ══════════════════════════════════════════════════════════════════════════════
class BackendError(Exception):
    def __init__(self, error: dict):
        super().__init__(error.get("message", "Backend error"))
        self.error = error


def make_error(kind, layer, message, status=None, detail=None):
    return {"kind": kind, "layer": layer, "message": message, "status": status, "detail": detail}


def infer_layer(status, detail):
    """Best-effort guess of which layer failed, based on the error text sent by the backend."""
    text = (detail or "").lower()
    if any(word in text for word in ("model", "predictor", "predict_congestion", "random_forest",
                                     "sklearn", "joblib", "pickle")):
        return "ml_model"
    if any(word in text for word in ("tomtom", "openweather", "weather", "traffic api", "upstream")):
        return "data_source"
    return "backend"


def short_reason(error):
    """One short phrase for cards and pipeline rows (the full message is shown once at the top)."""
    kind = error.get("kind")
    if kind == "connection":
        return "backend not reachable"
    if kind == "timeout":
        return "backend timed out"
    if kind == "invalid_json":
        return "invalid backend response"
    if kind == "schema":
        return "unexpected response format"
    if kind == "model":
        return "model unavailable"
    if kind == "http":
        prefix = {"ml_model": "model error", "data_source": "data source error"}.get(error.get("layer"), "backend error")
        return f"{prefix} (HTTP {error.get('status')})"
    return "request failed"


def explain_http(status, layer):
    if status in (401, 403):
        return ("The request was rejected as unauthorised. If this comes from TomTom or OpenWeather, "
                "the API key configured in the backend (.env or deployment secrets) may be wrong.")
    if status == 404:
        return "Endpoint not found. Check BACKEND_URL and that the backend exposes this route."
    if status == 422:
        return ("The backend rejected the request parameters or body (validation error). "
                "The frontend payload may not match the backend schema.")
    if status == 429:
        return "Rate limit exceeded. Wait a moment and press Refresh."
    if status >= 500:
        if layer == "ml_model":
            return "The ML model failed or is unavailable."
        if layer == "data_source":
            return "A data source (TomTom / OpenWeather) failed, as reported by the backend."
        return "The backend returned a server error."
    return f"The backend returned HTTP {status}."


def _extract_detail(response):
    try:
        body = response.json()
    except ValueError:
        return (response.text or "").strip()[:300] or None
    if isinstance(body, dict):
        for key in ("detail", "message", "error"):
            if body.get(key):
                return str(body[key])[:300]
        return json.dumps(body)[:300]
    return str(body)[:300]


def call_backend(base_url, method, path, *, params=None, json_body=None, timeout=10.0):
    """
    Call the FastAPI backend. Always returns a dict:
      {"ok": True,  "data": <parsed JSON>, "status": 200, "fetched_at": <iso string>}
      {"ok": False, "error": {kind, layer, message, status, detail}}
    It never raises for network or HTTP problems, so the Streamlit app cannot crash on them.
    """
    url = f"{base_url.rstrip('/')}{path}"
    try:
        response = requests.request(method, url, params=params, json=json_body, timeout=timeout)
    except requests.exceptions.Timeout:
        return {"ok": False, "error": make_error(
            "timeout", "backend", f"The backend did not respond within {timeout:g} seconds.", detail=url)}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": make_error(
            "connection", "backend",
            "Could not connect to the backend. It may be down or not started, BACKEND_URL may be "
            "wrong, or there may be no network connection.", detail=url)}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": make_error(
            "request", "backend", f"The request to the backend failed ({exc.__class__.__name__}).",
            detail=str(exc)[:300])}

    if response.status_code >= 400:
        detail = _extract_detail(response)
        layer = infer_layer(response.status_code, detail)
        return {"ok": False, "error": make_error(
            "http", layer, explain_http(response.status_code, layer),
            status=response.status_code, detail=detail)}

    try:
        data = response.json()
    except ValueError:
        return {"ok": False, "error": make_error(
            "invalid_json", "backend", "The backend response was not valid JSON.",
            status=response.status_code, detail=(response.text or "")[:200])}

    if not isinstance(data, (dict, list)):
        return {"ok": False, "error": make_error(
            "schema", "backend", "The backend response was not a JSON object.",
            status=response.status_code)}

    return {"ok": True, "data": data, "status": response.status_code,
            "fetched_at": datetime.now(IST).isoformat(timespec="seconds")}


# ══════════════════════════════════════════════════════════════════════════════
# TOLERANT RESPONSE PARSING  (Task Four)
# The exact JSON layout of /api/v1/data/current has to be verified against the real
# backend. These helpers look for the usual key names (snake_case / camelCase, flat or
# nested under "traffic" / "weather"). Anything not found stays None — never a default.
# ══════════════════════════════════════════════════════════════════════════════
def _norm_key(key) -> str:
    return str(key).replace("_", "").replace("-", "").replace(" ", "").lower()


def find_value(obj, names, max_depth=4):
    """Depth-first search for the first non-null value whose key matches one of `names`."""
    wanted = {_norm_key(n) for n in names}

    def walk(node, depth):
        if depth > max_depth:
            return None
        if isinstance(node, dict):
            for key, value in node.items():
                if _norm_key(key) in wanted and value is not None:
                    return value
            for value in node.values():
                if isinstance(value, (dict, list)):
                    found = walk(value, depth + 1)
                    if found is not None:
                        return found
        elif isinstance(node, list):
            for item in node[:5]:
                found = walk(item, depth + 1)
                if found is not None:
                    return found
        return None

    return walk(obj, 0)


def to_float(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return number if math.isfinite(number) else None
    return None


def numeric_from(value, keys=()):
    """A number from a scalar, or from a small dict such as {"speed": 3.4} / {"1h": 0.5}."""
    if isinstance(value, dict):
        for wanted in keys:
            for key, inner in value.items():
                if _norm_key(key) == _norm_key(wanted):
                    number = to_float(inner)
                    if number is not None:
                        return number
        for inner in value.values():
            number = to_float(inner)
            if number is not None:
                return number
        return None
    return to_float(value)


def text_from(value):
    """Text from a string, or from OpenWeather-style [{"main": ..., "description": ...}]."""
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list) and value:
        return text_from(value[0])
    if isinstance(value, dict):
        for key in ("description", "main", "condition", "text"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
    return None


def _section(payload, names):
    found = find_value(payload, names)
    return found if isinstance(found, dict) else payload


def parse_current(payload):
    """Extract traffic + weather fields from the /api/v1/data/current response."""
    traffic_src = _section(payload, ("traffic", "traffic_data", "tomtom"))
    weather_src = _section(payload, ("weather", "weather_data", "openweather"))

    traffic = {
        "current_speed": to_float(find_value(traffic_src, ["current_speed", "currentSpeed"])),
        "free_flow_speed": to_float(find_value(
            traffic_src, ["free_flow_speed", "freeFlowSpeed", "freeflow_speed"])),
        "current_travel_time": to_float(find_value(
            traffic_src, ["current_travel_time", "currentTravelTime"])),
        "free_flow_travel_time": to_float(find_value(
            traffic_src, ["free_flow_travel_time", "freeFlowTravelTime"])),
    }
    weather = {
        "temperature": numeric_from(
            find_value(weather_src, ["temperature", "temp", "temperature_c"]), ("temp",)),
        "humidity": numeric_from(find_value(weather_src, ["humidity"])),
        "condition": text_from(find_value(
            weather_src, ["condition", "weather_condition", "weather_description",
                          "description", "weather"])),
        "rainfall": numeric_from(
            find_value(weather_src, ["rainfall", "rain_1h", "rain", "precipitation"]), ("1h", "3h")),
        "wind_speed": numeric_from(
            find_value(weather_src, ["wind_speed", "windSpeed", "wind"]), ("speed",)),
    }
    return {
        "traffic": traffic,
        "weather": weather,
        "collected_at": find_value(payload, ["collected_at", "collectedAt", "timestamp"]),
        "reported_location": find_value(payload, ["location"], max_depth=1),
        "has_any_field": any(v is not None for v in traffic.values())
                         or any(v is not None for v in weather.values()),
    }


def parse_prediction(payload):
    """Extract the fields the backend promises: location, prediction, confidence, source, collected_at."""
    def top(*names):
        return find_value(payload, names, max_depth=1)

    return {
        "location": top("location"),
        "prediction": top("prediction", "predicted_congestion", "congestion_level"),
        "confidence": top("confidence"),
        "source": top("source"),
        "collected_at": top("collected_at", "collectedAt", "timestamp"),
        "error": top("error", "detail"),
    }


def prediction_label(value):
    """Show the model output exactly as returned (categories must match the ML team's output)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, dict):
        for key in ("label", "level", "congestion_level", "class", "category"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
        return json.dumps(value)
    return None


def format_confidence(value):
    """Confidence as a percentage, only if the model supplied a number."""
    number = to_float(value)
    if number is None:
        return None
    if 0 <= number <= 1:
        return f"{number * 100:.0f}%"
    if 1 < number <= 100:
        return f"{number:.0f}%"
    return str(value)


def prediction_color(label):
    """Colour only — the text shown is always the model's own label."""
    text = (label or "").lower()
    if any(word in text for word in ("high", "severe", "heavy")):
        return "#f54242"
    if any(word in text for word in ("moderate", "medium")):
        return "#f58542"
    if any(word in text for word in ("low", "light", "free")):
        return "#34d47a"
    return "#7b82a0"


def location_mismatch(requested_name, reported):
    """True if the backend says the data is for a different place than the one requested."""
    if isinstance(reported, dict):
        reported = reported.get("name") or reported.get("city")
    if not isinstance(reported, str) or not reported.strip():
        return False
    return requested_name.lower() not in reported.lower()


# ══════════════════════════════════════════════════════════════════════════════
# TIME + DISTANCE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def parse_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def fmt_ts(value):
    """Readable timestamp. Timezone-aware values are shown in IST; unparsable text is shown as-is."""
    if value is None or str(value).strip() == "":
        return UNAVAILABLE
    parsed = parse_ts(value)
    if parsed is None:
        return str(value)
    if parsed.tzinfo is not None:
        return parsed.astimezone(IST).strftime("%d %b %Y, %H:%M:%S IST")
    return parsed.strftime("%d %b %Y, %H:%M:%S")


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line (great-circle) distance — NOT a road distance."""
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════════════════════
# HISTORICAL CSV  (Task Seven)
# Real rows from the project's collected CSV only. If the file is missing, empty or has
# no rows for the location, a message is returned instead — never generated history.
# ══════════════════════════════════════════════════════════════════════════════
def load_history(path, location_name=None, max_points=500):
    result = {"df": None, "message": None, "note": None, "has_free_flow": False}

    if not path or not os.path.isfile(path):
        result["message"] = HISTORY_UNAVAILABLE
        return result
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # unreadable / malformed file must not crash the app
        result["message"] = f"The historical CSV could not be read ({exc.__class__.__name__})."
        return result

    columns = {_norm_key(c): c for c in df.columns}

    def pick(candidates):
        for candidate in candidates:
            if _norm_key(candidate) in columns:
                return columns[_norm_key(candidate)]
        return None

    time_col = pick(["timestamp_utc", "collected_at", "timestamp", "datetime", "date_time", "time", "date"])
    speed_col = pick(["current_speed_kmph", "current_speed", "currentspeed", "speed", "avg_speed"])
    free_col = pick(["free_flow_speed_kmph", "free_flow_speed", "freeflowspeed", "freeflow_speed"])
    loc_col = pick(["location", "location_name", "road", "road_name", "name"])

    if time_col is None or speed_col is None:
        result["message"] = ("The historical CSV was found but has no recognisable time and speed "
                             f"columns (columns found: {', '.join(map(str, df.columns))}).")
        return result

    frame = pd.DataFrame({
        "time": pd.to_datetime(df[time_col], errors="coerce"),
        "speed": pd.to_numeric(df[speed_col], errors="coerce"),
    })
    if free_col is not None:
        frame["free_flow"] = pd.to_numeric(df[free_col], errors="coerce")

    if loc_col is not None and location_name:
        mask = df[loc_col].astype(str).str.lower().str.contains(location_name.lower(), regex=False)
        frame = frame[mask.values]
    elif loc_col is None:
        result["note"] = ("The CSV has no location column, so the rows could not be filtered "
                          "by location — all rows are shown.")

    frame = frame.dropna(subset=["time", "speed"]).sort_values("time")
    if len(frame) < 2:
        result["message"] = HISTORY_UNAVAILABLE
        return result

    frame = frame.tail(max_points)
    result["df"] = frame
    result["has_free_flow"] = "free_flow" in frame.columns and frame["free_flow"].notna().any()
    return result
