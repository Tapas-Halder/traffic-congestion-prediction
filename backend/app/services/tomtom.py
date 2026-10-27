"""TomTom Traffic Flow client. Never expose an API key or complete request URL."""
import logging
import requests
from app.config import settings

logger = logging.getLogger(__name__)
TOMTOM_FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"

class TrafficSourceError(RuntimeError):
    pass

def get_traffic_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    if not settings.tomtom_api_key:
        raise TrafficSourceError("TomTom API key is not configured in Render.")
    lat = latitude if latitude is not None else settings.latitude
    lon = longitude if longitude is not None else settings.longitude
    try:
        response = requests.get(TOMTOM_FLOW_URL,
            params={"point": f"{lat},{lon}", "unit": "KMPH", "key": settings.tomtom_api_key},
            timeout=settings.request_timeout)
        if response.status_code in (401, 403):
            raise TrafficSourceError("TomTom denied Traffic Flow access (HTTP %s). Check key validity, Traffic Flow product permissions and quota in TomTom Developer Portal; rotate any exposed key." % response.status_code)
        if response.status_code == 429:
            raise TrafficSourceError("TomTom rate limit reached (HTTP 429). Try again later.")
        if response.status_code >= 400:
            raise TrafficSourceError("TomTom Traffic Flow request failed (HTTP %s)." % response.status_code)
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("flowSegmentData"), dict):
            raise TrafficSourceError("TomTom response did not contain traffic flow data.")
        return data
    except requests.exceptions.Timeout as exc:
        raise TrafficSourceError("TomTom request timed out.") from exc
    except requests.exceptions.RequestException as exc:
        raise TrafficSourceError("TomTom network request failed.") from exc
    except ValueError as exc:
        raise TrafficSourceError("TomTom returned invalid JSON.") from exc
