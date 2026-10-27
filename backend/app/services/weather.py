"""OpenWeather client. Never expose API credentials in error responses."""
import requests
from app.config import settings

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherSourceError(RuntimeError):
    pass

def get_weather_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    if not settings.openweather_api_key:
        raise WeatherSourceError("OpenWeather API key is not configured in Render.")
    lat = latitude if latitude is not None else settings.latitude
    lon = longitude if longitude is not None else settings.longitude
    try:
        response = requests.get(OPENWEATHER_URL,
            params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric"},
            timeout=settings.request_timeout)
        if response.status_code in (401, 403):
            raise WeatherSourceError("OpenWeather denied access (HTTP %s). Check API key and plan." % response.status_code)
        if response.status_code == 429:
            raise WeatherSourceError("OpenWeather rate limit reached (HTTP 429).")
        if response.status_code >= 400:
            raise WeatherSourceError("OpenWeather request failed (HTTP %s)." % response.status_code)
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("main"), dict):
            raise WeatherSourceError("OpenWeather response is missing weather fields.")
        return data
    except requests.exceptions.Timeout as exc:
        raise WeatherSourceError("OpenWeather request timed out.") from exc
    except requests.exceptions.RequestException as exc:
        raise WeatherSourceError("OpenWeather network request failed.") from exc
    except ValueError as exc:
        raise WeatherSourceError("OpenWeather returned invalid JSON.") from exc
