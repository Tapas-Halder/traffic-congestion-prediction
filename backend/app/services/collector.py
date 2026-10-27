"""Collect traffic and weather independently; a TomTom 403 must not hide real weather."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from app.services.tomtom import get_traffic_data, TrafficSourceError
from app.services.weather import get_weather_data, WeatherSourceError

def collect_current_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    with ThreadPoolExecutor(max_workers=2) as pool:
        traffic_future = pool.submit(get_traffic_data, latitude, longitude)
        weather_future = pool.submit(get_weather_data, latitude, longitude)
        results = {}
        errors = {}
        for name, future, error_type in (
            ("traffic", traffic_future, TrafficSourceError),
            ("weather", weather_future, WeatherSourceError),
        ):
            try:
                results[name] = future.result()
            except error_type as exc:
                results[name] = None
                errors[name] = str(exc)
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "location": {"latitude": latitude, "longitude": longitude},
        "traffic": results["traffic"],
        "weather": results["weather"],
        "source_errors": errors,
    }
