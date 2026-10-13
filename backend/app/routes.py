"""Road routing with TomTom primary, OSRM fallback and sampled TomTom traffic."""
import logging
import requests
from fastapi import APIRouter, HTTPException, Query
from app.config import settings
from app.services.tomtom import get_traffic_data

logger = logging.getLogger(__name__)
router = APIRouter()
ROUTING_URL = "https://api.tomtom.com/routing/1/calculateRoute/{points}/json"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}"

def _status(flow):
    current, free = flow.get("currentSpeed"), flow.get("freeFlowSpeed")
    if not isinstance(current, (int, float)) or not isinstance(free, (int, float)) or free <= 0:
        return "unavailable"
    ratio = current / free
    return "low" if ratio >= .90 else "moderate" if ratio >= .70 else "heavy"

@router.get("/api/v1/route")
def get_route(
    from_lat: float = Query(ge=-90, le=90),
    from_lon: float = Query(ge=-180, le=180),
    to_lat: float = Query(ge=-90, le=90),
    to_lon: float = Query(ge=-180, le=180),
):
    if not settings.tomtom_api_key:
        raise HTTPException(503, detail="TomTom API key is not configured")
    if abs(from_lat - to_lat) + abs(from_lon - to_lon) < 1e-7:
        raise HTTPException(422, detail="Choose different start and destination points")
    points = f"{from_lat},{from_lon}:{to_lat},{to_lon}"
    provider = "tomtom"
    try:
        response = requests.get(
            ROUTING_URL.format(points=points),
            params={"key": settings.tomtom_api_key, "traffic": "true",
                    "travelMode": "car", "routeType": "fastest"},
            timeout=max(15, settings.request_timeout),
        )
        response.raise_for_status()
        data = response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status not in (401, 403):
            logger.warning("TomTom Routing HTTP %s", status)
            raise HTTPException(502, detail={"error": "tomtom_routing_http_error", "upstream_status": status}) from exc
        logger.warning("TomTom Routing HTTP %s; trying OSRM fallback", status)
        provider = "osrm"
    except requests.RequestException as exc:
        logger.exception("TomTom Routing network request failed")
        raise HTTPException(502, detail="TomTom Routing network request failed") from exc

    if provider == "tomtom":
        routes = data.get("routes") or []
        if not routes:
            raise HTTPException(502, detail="TomTom returned no drivable road route")
        route = routes[0]
        coords = [[p["latitude"], p["longitude"]] for leg in route.get("legs", []) for p in leg.get("points", [])]
        summary = route.get("summary", {})
        distance = summary.get("lengthInMeters")
        travel_time = summary.get("travelTimeInSeconds")
        delay = summary.get("trafficDelayInSeconds")
    else:
        try:
            fallback = requests.get(
                OSRM_URL.format(from_lon=from_lon, from_lat=from_lat, to_lon=to_lon, to_lat=to_lat),
                params={"overview": "full", "geometries": "geojson", "steps": "false"},
                timeout=20,
            )
            fallback.raise_for_status()
            result = fallback.json()
            if result.get("code") != "Ok" or not result.get("routes"):
                raise ValueError("OSRM returned no drivable route")
            route = result["routes"][0]
            coords = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
            distance = route.get("distance")
            # OSRM duration is not a live traffic-aware ETA.
            travel_time = None
            delay = None
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            logger.exception("OSRM fallback failed")
            raise HTTPException(502, detail="TomTom Routing access denied and OSRM fallback unavailable") from exc

    if len(coords) < 2:
        raise HTTPException(502, detail="Road route geometry is unavailable")
    # At most 6 sampling calls per selected route to limit quota usage.
    # These are *sampled point observations*, not full road-segment coverage.
    sample_count = min(6, max(2, len(coords) // 25))
    indices = sorted(set(round(i * (len(coords) - 1) / (sample_count - 1)) for i in range(sample_count)))
    samples = []
    for index in indices:
        lat, lon = coords[index]
        status = "unavailable"
        try:
            raw = get_traffic_data(lat, lon)
            status = _status(raw.get("flowSegmentData") or {})
        except (requests.RequestException, ValueError, KeyError, RuntimeError):
            logger.warning("Traffic flow sample unavailable for route point %s", index)
        samples.append({"index": index, "status": status})
    return {
        "coordinates": coords, "samples": samples,
        "distance_meters": distance,
        "travel_time_seconds": travel_time,
        "traffic_delay_seconds": delay,
        "route_provider": provider,
        "traffic_source": "TomTom Flow API sampled along road route",
        "coverage": "sampled_estimate",
    }
