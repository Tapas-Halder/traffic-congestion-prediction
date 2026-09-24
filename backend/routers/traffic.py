from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
from fastapi import APIRouter, HTTPException
from schemas.traffic import PredictionRequest, PredictionResponse
from services.predictor import predictor
from services.tomtom import get_traffic, get_route
from services.weather import get_weather
from services.history import add_snapshot, get_snapshots
from config import DEFAULT_LAT, DEFAULT_LON

router = APIRouter(prefix="/api", tags=["traffic"])

KOLKATA_LOCATIONS = {
    "Howrah Station": (22.5839, 88.3428),
    "Sealdah Station": (22.5646, 88.3691),
    "Esplanade": (22.5667, 88.3533),
    "Park Street": (22.5535, 88.3520),
    "Salt Lake Sector V": (22.5750, 88.4330),
    "New Town": (22.5958, 88.4797),
    "Airport": (22.6547, 88.4467),
    "Dum Dum": (22.6225, 88.3773),
    "Garia": (22.4676, 88.3731),
    "Jadavpur": (22.4992, 88.3691),
    "Behala": (22.4987, 88.3210),
    "Alipore": (22.5310, 88.3310),
    "Tollygunge": (22.4988, 88.3498),
    "Ballygunge": (22.5334, 88.3650),
    "Science City": (22.5395, 88.3960),
    "Rajarhat": (22.6215, 88.4560),
}

def straight_distance_km(a, b):
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * atan2(sqrt(h), sqrt(max(1 - h, 0)))

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/locations")
def locations():
    return {"locations": list(KOLKATA_LOCATIONS.keys())}

@router.post("/predict", response_model=PredictionResponse)
def predict(p: PredictionRequest):
    hour = p.hour if p.hour is not None else datetime.now().hour
    level, probability, speed = predictor.predict_current(
        p.speed, p.free_flow_speed, hour, {"rain_1h": p.weather}
    )
    return {
        "congestion_level": level,
        "probability": probability,
        "predicted_speed": speed,
    }

@router.get("/live")
async def live(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON):
    try:
        data = (await get_traffic(lat, lon)).get("flowSegmentData", {})
        return {
            "latitude": lat,
            "longitude": lon,
            "current_speed": data.get("currentSpeed"),
            "free_flow_speed": data.get("freeFlowSpeed"),
            "confidence": data.get("confidence"),
            "road_closure": data.get("roadClosure", False),
        }
    except Exception as exc:
        raise HTTPException(502, f"Live traffic service error: {exc}")

@router.get("/weather")
async def weather(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON):
    try:
        return await get_weather(lat, lon)
    except Exception as exc:
        raise HTTPException(502, f"Weather service error: {exc}")

@router.get("/route-history")
def route_history(origin: str, destination: str):
    if origin not in KOLKATA_LOCATIONS or destination not in KOLKATA_LOCATIONS:
        raise HTTPException(400, "Please select valid Kolkata locations.")
    return {"items": get_snapshots(origin, destination)}

@router.get("/route-predict")
async def route_predict(origin: str, destination: str):
    if origin not in KOLKATA_LOCATIONS or destination not in KOLKATA_LOCATIONS:
        raise HTTPException(400, "Please select valid Kolkata locations.")
    if origin == destination:
        raise HTTPException(400, "Origin and destination must be different.")

    start = KOLKATA_LOCATIONS[origin]
    end = KOLKATA_LOCATIONS[destination]
    now = datetime.now(timezone.utc)

    try:
        flow = (await get_traffic(*start)).get("flowSegmentData", {})
        live_speed = float(flow.get("currentSpeed") or 0)
        live_free_flow = float(flow.get("freeFlowSpeed") or 0)
    except Exception as exc:
        raise HTTPException(502, f"TomTom traffic API error: {exc}")

    if live_speed <= 0 or live_free_flow <= 0:
        raise HTTPException(502, "TomTom returned no live speed. Please try again.")

    try:
        route_data = await get_route(start, end)
        route = (route_data.get("routes") or [None])[0]
        if not route:
            raise RuntimeError("TomTom returned no route.")

        summary = route.get("summary", {})
        distance_m = max(float(summary.get("lengthInMeters") or 0), 1)
        travel_time = max(float(summary.get("travelTimeInSeconds") or 0), 1)
        traffic_delay = max(float(summary.get("trafficDelayInSeconds") or 0), 0)
        no_traffic_time = max(float(summary.get("noTrafficTravelTimeInSeconds") or 0), 1)

        points = []
        for leg in route.get("legs", []):
            for point in leg.get("points", []):
                if "latitude" in point and "longitude" in point:
                    points.append({"lat": point["latitude"], "lon": point["longitude"]})

        current_speed = live_speed
        free_flow_speed = max(live_free_flow, (distance_m / no_traffic_time) * 3.6)
    except Exception:
        distance_m = straight_distance_km(start, end) * 1000
        current_speed = live_speed
        free_flow_speed = live_free_flow
        travel_time = distance_m / max(current_speed / 3.6, 1)
        no_traffic_time = distance_m / max(free_flow_speed / 3.6, 1)
        traffic_delay = max(0, travel_time - no_traffic_time)
        points = [
            {"lat": start[0], "lon": start[1]},
            {"lat": end[0], "lon": end[1]},
        ]

    try:
        weather = await get_weather(*end)
        weather_status = "live"
    except Exception:
        weather = {
            "temperature": 27,
            "feels_like": 27,
            "humidity": 70,
            "pressure": 1012,
            "description": "Weather data unavailable",
            "icon": None,
            "clouds": 0,
            "rain_1h": 0,
            "snow_1h": 0,
            "wind_speed": 0,
            "visibility": 10000,
            "weather_impact": 0,
            "observed_at": None,
        }
        weather_status = "fallback"

    history = [
        x["current_speed"]
        for x in get_snapshots(origin, destination)
        if x.get("current_speed") is not None
    ]

    local_now = datetime.now()
    level, probability, predicted_speed = predictor.predict_current(
        current_speed,
        max(free_flow_speed, current_speed),
        local_now.hour,
        weather,
        history,
        local_now.weekday(),
    )
    forecast = predictor.forecast(
        current_speed,
        max(free_flow_speed, current_speed),
        local_now.hour,
        weather,
        history,
        local_now.weekday(),
    )

    result = {
        "origin": origin,
        "destination": destination,
        "distance_km": round(distance_m / 1000, 2),
        "travel_time_min": round(travel_time / 60, 1),
        "traffic_delay_min": round(traffic_delay / 60, 1),
        "current_speed": round(current_speed, 1),
        "free_flow_speed": round(free_flow_speed, 1),
        "predicted_speed": predicted_speed,
        "congestion_level": level,
        "probability": probability,
        "weather": weather,
        "weather_status": weather_status,
        "forecast": forecast,
        "route_points": points,
        "updated_at": now.isoformat(),
    }

    add_snapshot(origin, destination, result)
    return result

@router.get("/model-metrics")
def model_metrics():
    return predictor.model_metrics()
