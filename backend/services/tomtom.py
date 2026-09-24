import httpx
from config import TOMTOM_API_KEY

FLOW_URL="https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
ROUTE_URL="https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"

async def get_traffic(lat, lon):
    if not TOMTOM_API_KEY:
        raise RuntimeError("TOMTOM_API_KEY is not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        response=await client.get(
            FLOW_URL,
            params={"point": f"{lat},{lon}", "key": TOMTOM_API_KEY},
        )
        response.raise_for_status()
        return response.json()

async def get_route(origin, destination):
    if not TOMTOM_API_KEY:
        raise RuntimeError("TOMTOM_API_KEY is not configured")
    locations=f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}"
    async with httpx.AsyncClient(timeout=20) as client:
        response=await client.get(
            ROUTE_URL.format(locations=locations),
            params={
                "key": TOMTOM_API_KEY,
                "traffic": "true",
                "travelMode": "car",
                "routeType": "fastest",
            },
        )
        response.raise_for_status()
        return response.json()
