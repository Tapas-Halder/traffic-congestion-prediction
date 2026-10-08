"""Collect real-world Kolkata traffic and weather data into a CSV file.

This script uses TomTom Traffic Flow API and OpenWeather API.
API keys are read from environment variables and are never stored in the CSV.
"""
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

KOLKATA_LAT = 22.5726
KOLKATA_LON = 88.3639
TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "kolkata_traffic_weather.csv"

FIELDS = [
    "timestamp_utc", "city", "latitude", "longitude",
    "current_speed_kmph", "free_flow_speed_kmph", "current_travel_time_sec",
    "free_flow_travel_time_sec", "confidence", "road_closure",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_mps", "rain_1h_mm", "weather_main", "weather_description"
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


def fetch_traffic(api_key: str) -> dict:
    params = {
        "point": f"{KOLKATA_LAT},{KOLKATA_LON}",
        "unit": "KMPH",
        "key": api_key,
    }
    response = create_session().get(TRAFFIC_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["flowSegmentData"]


def fetch_weather(api_key: str) -> dict:
    params = {
        "lat": KOLKATA_LAT,
        "lon": KOLKATA_LON,
        "appid": api_key,
        "units": "metric",
    }
    response = create_session().get(WEATHER_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def build_row(traffic: dict, weather: dict) -> dict:
    rain = weather.get("rain", {}).get("1h", 0.0)
    current = traffic.get("currentSpeed")
    free_flow = traffic.get("freeFlowSpeed")

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "city": "Kolkata",
        "latitude": KOLKATA_LAT,
        "longitude": KOLKATA_LON,
        "current_speed_kmph": current,
        "free_flow_speed_kmph": free_flow,
        "current_travel_time_sec": traffic.get("currentTravelTime"),
        "free_flow_travel_time_sec": traffic.get("freeFlowTravelTime"),
        "confidence": traffic.get("confidence"),
        "road_closure": traffic.get("roadClosure"),
        "temperature_c": weather.get("main", {}).get("temp"),
        "feels_like_c": weather.get("main", {}).get("feels_like"),
        "humidity_pct": weather.get("main", {}).get("humidity"),
        "pressure_hpa": weather.get("main", {}).get("pressure"),
        "wind_speed_mps": weather.get("wind", {}).get("speed"),
        "rain_1h_mm": rain,
        "weather_main": (weather.get("weather") or [{}])[0].get("main"),
        "weather_description": (weather.get("weather") or [{}])[0].get("description"),
    }


def append_row(row: dict) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    traffic_key = get_env("TOMTOM_API_KEY")
    weather_key = get_env("OPENWEATHER_API_KEY")

    traffic = fetch_traffic(traffic_key)
    weather = fetch_weather(weather_key)
    row = build_row(traffic, weather)
    append_row(row)

    print("Collected 1 Kolkata traffic/weather row.")
    print(f"CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
