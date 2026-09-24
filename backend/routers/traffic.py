import asyncio
from datetime import datetime, timezone
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

def route_points(route):
    points = []
    for leg in route.get("legs", []):
        for point in leg.get("points", []):
            if "latitude" in point and "longitude" in point:
                points.append({"lat": point["latitude"], "lon": point["longitude"]})
    return points

def route_summary(route):
    summary = route.get("summary", {})
    distance_m = max(float(summary.get("lengthInMeters") or 0), 1)
    travel_time = max(float(summary.get("travelTimeInSeconds") or 0), 1)
    delay = max(float(summary.get("trafficDelayInSeconds") or 0), 0)
    no_traffic = max(float(summary.get("noTrafficTravelTimeInSeconds") or 0), 1)
    return distance_m, travel_time, delay, no_traffic

def congestion_level(speed, free_flow):
    ratio = speed / max(free_flow, 1)
    if ratio >= 0.80:
        return "Free Flow"
    if ratio >= 0.60:
        return "Moderate"
    if ratio >= 0.40:
        return "Heavy"
    return "Severe"

def extract_road_candidates(route):
    guidance = route.get("guidance", {})
    instructions = guidance.get("instructions", []) or []
    roads = []
    seen = set()

    for instruction in instructions:
        street = instruction.get("street") or ""
        road_numbers = instruction.get("roadNumbers") or []
        name = street.strip() if isinstance(street, str) else ""
        if not name and road_numbers:
            name = " / ".join(str(x) for x in road_numbers)
        if not name:
            continue

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        point = instruction.get("point") or {}
        if "latitude" in point and "longitude" in point:
            roads.append({
                "name": name,
                "road_numbers": road_numbers,
                "lat": float(point["latitude"]),
                "lon": float(point["longitude"]),
            })

    # Keep the UI fast while still showing the main roads used by the route.
    return roads[:8]

async def road_traffic(roads):
    async def one(road):
        try:
            data = (await get_traffic(road["lat"], road["lon"])).get("flowSegmentData", {})
            speed = float(data.get("currentSpeed") or 0)
            free = float(data.get("freeFlowSpeed") or 0)
            if speed <= 0 or free <= 0:
                raise RuntimeError("No speed data")
            return {
                "name": road["name"],
                "road_numbers": road["road_numbers"],
                "current_speed": round(speed, 1),
                "free_flow_speed": round(free, 1),
                "congestion_level": congestion_level(speed, free),
                "confidence": data.get("confidence"),
                "road_closure": bool(data.get("roadClosure", False)),
            }
        except Exception:
            return {
                "name": road["name"],
                "road_numbers": road["road_numbers"],
                "current_speed": None,
                "free_flow_speed": None,
                "congestion_level": "Unknown",
                "confidence": None,
                "road_closure": False,
            }

    results = await asyncio.gather(*(one(r) for r in roads))
    return [x for x in results if x["current_speed"] is not None]

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
        route_data = await get_route(start, end)
    except Exception as exc:
        raise HTTPException(
            502,
            f"TomTom route service error: {exc}. The map will not draw a fake straight line."
        )

    routes = route_data.get("routes") or []
    if not routes:
        raise HTTPException(502, "TomTom returned no drivable route.")

    # TomTom returns routes in decreasing optimality for this request.
    route_cards = []
    for index, route in enumerate(routes):
        distance_m, travel_time, delay, no_traffic = route_summary(route)
        route_cards.append({
            "route_index": index,
            "label": "Fastest" if index == 0 else f"Alternative {index}",
            "distance_km": round(distance_m / 1000, 2),
            "travel_time_min": round(travel_time / 60, 1),
            "traffic_delay_min": round(delay / 60, 1),
            "no_traffic_time_min": round(no_traffic / 60, 1),
            "traffic_status": "Delayed" if delay > 60 else "Moving",
            "route_points": route_points(route),
        })

    # The first route is the fastest route returned by TomTom for routeType=fastest.
    selected = routes[0]
    distance_m, travel_time, traffic_delay, no_traffic_time = route_summary(selected)

    road_candidates = extract_road_candidates(selected)
    road_data = await road_traffic(road_candidates)

    # Prefer actual road-level traffic at the first named road. If unavailable,
    # use the route summary's traffic-adjusted speed.
    if road_data:
        current_speed = road_data[0]["current_speed"]
        free_flow_speed = road_data[0]["free_flow_speed"]
    else:
        current_speed = (distance_m / travel_time) * 3.6
        free_flow_speed = (distance_m / no_traffic_time) * 3.6

    try:
        weather = await get_weather(*end)
        weather_status = "live"
    except Exception:
        weather = {
            "temperature": 27, "feels_like": 27, "humidity": 70, "pressure": 1012,
            "description": "Weather data unavailable", "icon": None, "clouds": 0,
            "rain_1h": 0, "snow_1h": 0, "wind_speed": 0, "visibility": 10000,
            "weather_impact": 0, "observed_at": None,
        }
        weather_status = "fallback"

    history = [
        x["current_speed"]
        for x in get_snapshots(origin, destination)
        if x.get("current_speed") is not None
    ]

    local_now = datetime.now()
    level, probability, predicted_speed = predictor.predict_current(
        current_speed, max(free_flow_speed, current_speed), local_now.hour,
        weather, history, local_now.weekday()
    )
    forecast = predictor.forecast(
        current_speed, max(free_flow_speed, current_speed), local_now.hour,
        weather, history, local_now.weekday()
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
        "route_points": route_points(selected),
        "roads": road_data,
        "routes": route_cards,
        "selected_route_index": 0,
        "route_source": "TomTom Routing + Traffic",
        "updated_at": now.isoformat(),
    }

    add_snapshot(origin, destination, result)
    return result

@router.get("/model-metrics")
def model_metrics():
    return predictor.model_metrics()
