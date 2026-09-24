import httpx
from config import TOMTOM_API_KEY

FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
ROUTE_URL = "https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{locations}"


async def get_traffic(lat, lon):
    if not TOMTOM_API_KEY:
        raise RuntimeError("TOMTOM_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            FLOW_URL,
            params={"point": f"{lat},{lon}", "key": TOMTOM_API_KEY},
        )
        response.raise_for_status()
        return response.json()


async def _get_tomtom_route(origin, destination):
    locations = f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "travelMode": "car",
        "routeType": "fastest",
        "maxAlternatives": 2,
        "alternativeType": "anyRoute",
        "computeTravelTimeFor": "all",
        "instructionsType": "text",
        "language": "en-GB",
        "routeRepresentation": "polyline",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(ROUTE_URL.format(locations=locations), params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("routes"):
            raise RuntimeError("TomTom returned no drivable route")
        return data


async def _get_osrm_fallback(origin, destination):
    # Real road geometry fallback. TomTom remains the primary route/traffic provider.
    locations = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    params = {"overview": "full", "geometries": "geojson", "steps": "false"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(OSRM_URL.format(locations=locations), params=params)
        response.raise_for_status()
        data = response.json()
    osrm_routes = data.get("routes") or []
    if not osrm_routes:
        raise RuntimeError("No road route was returned")
    r = osrm_routes[0]
    coords = (r.get("geometry") or {}).get("coordinates") or []
    points = [{"latitude": c[1], "longitude": c[0]} for c in coords if len(c) >= 2]
    if len(points) < 2:
        raise RuntimeError("Road route geometry is unavailable")
    return {
        "routes": [{
            "summary": {
                "lengthInMeters": r.get("distance", 0),
                "travelTimeInSeconds": r.get("duration", 0),
                "trafficDelayInSeconds": 0,
                "noTrafficTravelTimeInSeconds": r.get("duration", 0),
            },
            "legs": [{"points": points}],
            "guidance": {"instructions": []},
        }],
        "_fallback": True,
    }


async def get_route(origin, destination):
    if not TOMTOM_API_KEY:
        # Keep the app usable even before the user adds the optional TomTom key.
        return await _get_osrm_fallback(origin, destination)

    try:
        return await _get_tomtom_route(origin, destination)
    except Exception as tomtom_error:
        try:
            data = await _get_osrm_fallback(origin, destination)
            data["_tomtom_error"] = str(tomtom_error)
            return data
        except Exception:
            raise tomtom_error
