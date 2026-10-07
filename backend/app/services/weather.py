import requests
from app.config import settings

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    """Fetch current weather information for one Kolkata point."""
    if not settings.openweather_api_key:
        raise RuntimeError("OPENWEATHER_API_KEY is not configured")
    lat = latitude if latitude is not None else settings.latitude
    lon = longitude if longitude is not None else settings.longitude
    response = requests.get(
        OPENWEATHER_URL,
        params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric"},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    return response.json()
