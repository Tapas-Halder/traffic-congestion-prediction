import requests
from app.config import settings

TOMTOM_FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"

def get_traffic_data(latitude: float | None = None, longitude: float | None = None) -> dict:
    """Fetch current traffic-flow information for one Kolkata point."""
    if not settings.tomtom_api_key:
        raise RuntimeError("TOMTOM_API_KEY is not configured")
    lat = latitude if latitude is not None else settings.latitude
    lon = longitude if longitude is not None else settings.longitude
    response = requests.get(
        TOMTOM_FLOW_URL,
        params={"point": f"{lat},{lon}", "unit": "KMPH", "key": settings.tomtom_api_key},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    return response.json()
