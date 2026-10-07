from datetime import datetime, timezone
from app.services.tomtom import get_traffic_data
from app.services.weather import get_weather_data

def collect_current_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    """Collect traffic and weather data into one application payload."""
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "location": {"latitude": latitude, "longitude": longitude},
        "traffic": get_traffic_data(latitude, longitude),
        "weather": get_weather_data(latitude, longitude),
    }
