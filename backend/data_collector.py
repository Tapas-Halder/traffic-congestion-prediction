"""Collect real-world Kolkata traffic + weather data for multiple road checkpoints.

Traffic comes from TomTom Traffic Flow API.
Weather comes from OpenWeather API.
API keys are read from environment variables.

Important:
- TomTom flowSegmentData returns traffic for the road segment nearest to a
  supplied point. Therefore we monitor multiple points instead of one city
  coordinate.
- This is a representative Kolkata road network, not every single road.
- Add more checkpoints later if wider coverage is required.
"""
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "kolkata_traffic_weather.csv"

# Representative road checkpoints across major Kolkata corridors.
# Coordinates are points near major roads/junctions; TomTom returns the
# nearest traffic flow segment.
MONITOR_POINTS = [
    {"id": "H2S-01", "road": "Howrah Bridge", "corridor": "Howrah-Sector V", "lat": 22.58563, "lon": 88.34475},
    {"id": "H2S-02", "road": "Esplanade", "corridor": "Howrah-Sector V", "lat": 22.56250, "lon": 88.34983},
    {"id": "H2S-03", "road": "Park Circus", "corridor": "Howrah-Sector V", "lat": 22.53920, "lon": 88.37000},
    {"id": "H2S-04", "road": "Science City", "corridor": "Howrah-Sector V", "lat": 22.54004, "lon": 88.39601},
    {"id": "H2S-05", "road": "Chingrighata", "corridor": "Howrah-Sector V", "lat": 22.55070, "lon": 88.40409},
    {"id": "H2S-06", "road": "Sector V", "corridor": "Howrah-Sector V", "lat": 22.58132, "lon": 88.42982},
    {"id": "NORTH-01", "road": "Shyambazar", "corridor": "North Kolkata", "lat": 22.60100, "lon": 88.37400},
    {"id": "NORTH-02", "road": "Ultadanga", "corridor": "North Kolkata", "lat": 22.59613, "lon": 88.38528},
    {"id": "AIR-01", "road": "Airport / Jessore Road", "corridor": "Airport Corridor", "lat": 22.63951, "lon": 88.42978},
    {"id": "EAST-01", "road": "Ruby / EM Bypass", "corridor": "EM Bypass", "lat": 22.51478, "lon": 88.40147},
    {"id": "SOUTH-01", "road": "Garia / EM Bypass", "corridor": "EM Bypass", "lat": 22.46290, "lon": 88.39680},
    {"id": "CENTRAL-01", "road": "Park Street", "corridor": "Central Kolkata", "lat": 22.55350, "lon": 88.35200},
]

FIELDS = [
    "timestamp_utc", "city", "location_id", "road_name", "corridor",
    "latitude", "longitude",
    "current_speed_kmph", "free_flow_speed_kmph",
    "current_travel_time_sec", "free_flow_travel_time_sec",
    "confidence", "road_closure",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm", "weather_main", "weather_description",
]


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def fetch_traffic(session: requests.Session, api_key: str, point: dict) -> dict:
    params = {
        "point": f"{point['lat']},{point['lon']}",
        "unit": "KMPH",
        "key": api_key,
    }
    response = session.get(TRAFFIC_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["flowSegmentData"]


def fetch_weather(session: requests.Session, api_key: str) -> dict:
    params = {
        "lat": 22.5726,
        "lon": 88.3639,
        "appid": api_key,
        "units": "metric",
    }
    response = session.get(WEATHER_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def build_row(point: dict, traffic: dict, weather: dict, timestamp: str) -> dict:
    return {
        "timestamp_utc": timestamp,
        "city": "Kolkata",
        "location_id": point["id"],
        "road_name": point["road"],
        "corridor": point["corridor"],
        "latitude": point["lat"],
        "longitude": point["lon"],
        "current_speed_kmph": traffic.get("currentSpeed"),
        "free_flow_speed_kmph": traffic.get("freeFlowSpeed"),
        "current_travel_time_sec": traffic.get("currentTravelTime"),
        "free_flow_travel_time_sec": traffic.get("freeFlowTravelTime"),
        "confidence": traffic.get("confidence"),
        "road_closure": traffic.get("roadClosure"),
        "temperature_c": weather.get("main", {}).get("temp"),
        "feels_like_c": weather.get("main", {}).get("feels_like"),
        "humidity_pct": weather.get("main", {}).get("humidity"),
        "pressure_hpa": weather.get("main", {}).get("pressure"),
        "wind_speed_mps": weather.get("wind", {}).get("speed"),
        "rain_1h_mm": weather.get("rain", {}).get("1h", 0.0),
        "weather_main": (weather.get("weather") or [{}])[0].get("main"),
        "weather_description": (weather.get("weather") or [{}])[0].get("description"),
    }


def append_rows(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    traffic_key = get_env("TOMTOM_API_KEY")
    weather_key = get_env("OPENWEATHER_API_KEY")

    session = create_session()
    weather = fetch_weather(session, weather_key)
    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []
    failures = []

    for point in MONITOR_POINTS:
        try:
            traffic = fetch_traffic(session, traffic_key, point)
            rows.append(build_row(point, traffic, weather, timestamp))
            print(f"OK: {point['id']} - {point['road']}")
        except requests.RequestException as exc:
            failures.append(f"{point['id']}: {exc}")
            print(f"FAILED: {point['id']} - {exc}")

    if not rows:
        raise RuntimeError("No traffic checkpoint could be collected.")

    append_rows(rows)
    print(f"Collected {len(rows)} Kolkata road rows.")
    print(f"CSV: {CSV_PATH}")

    if failures:
        print(f"Warning: {len(failures)} checkpoint(s) failed this run.")


if __name__ == "__main__":
    main()
