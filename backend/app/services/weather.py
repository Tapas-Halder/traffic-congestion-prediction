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
    if response.status_code in (401, 403):
        raise RuntimeError(f"OpenWeather authentication/access denied (HTTP {response.status_code}).")
    if not response.ok:
        raise RuntimeError(f"OpenWeather request failed (HTTP {response.status_code}).")
    return response.json()
