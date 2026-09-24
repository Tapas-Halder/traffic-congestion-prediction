from datetime import datetime
from fastapi import APIRouter, HTTPException
from schemas.traffic import PredictionRequest, PredictionResponse
from services.predictor import predictor
from services.tomtom import get_traffic, get_route
from services.weather import get_weather
from config import DEFAULT_LAT, DEFAULT_LON

router=APIRouter(prefix="/api",tags=["traffic"])

KOLKATA_LOCATIONS={
    "Howrah Station":(22.5839,88.3428),
    "Sealdah Station":(22.5646,88.3699),
    "Esplanade":(22.5667,88.3533),
    "Park Street":(22.5535,88.3520),
    "Salt Lake Sector V":(22.5750,88.4330),
    "New Town":(22.5958,88.4797),
    "Airport":(22.6547,88.4467),
    "Dum Dum":(22.6225,88.3773),
    "Garia":(22.4676,88.3731),
    "Jadavpur":(22.4992,88.3691),
    "Behala":(22.4987,88.3210),
    "Alipore":(22.5310,88.3310),
    "Tollygunge":(22.4988,88.3498),
    "Ballygunge":(22.5334,88.3650),
    "Science City":(22.5395,88.3960),
    "Rajarhat":(22.6215,88.4560),
}

@router.get("/health")
def health():
    return {"status":"ok"}

@router.get("/locations")
def locations():
    return {"locations":list(KOLKATA_LOCATIONS.keys())}

@router.post("/predict",response_model=PredictionResponse)
def predict(p:PredictionRequest):
    level,prob,speed=predictor.predict(
        p.speed,p.free_flow_speed,
        p.hour if p.hour is not None else datetime.now().hour,
        p.weather
    )
    return {"congestion_level":level,"probability":prob,"predicted_speed":speed}

@router.get("/live")
async def live(lat:float=DEFAULT_LAT,lon:float=DEFAULT_LON):
    try:
        d=(await get_traffic(lat,lon)).get("flowSegmentData",{})
        return {
            "latitude":lat,"longitude":lon,
            "current_speed":d.get("currentSpeed"),
            "free_flow_speed":d.get("freeFlowSpeed"),
            "confidence":d.get("confidence"),
            "road_closure":d.get("roadClosure",False)
        }
    except Exception as e:
        raise HTTPException(502,str(e))

@router.get("/weather")
async def weather(lat:float=DEFAULT_LAT,lon:float=DEFAULT_LON):
    try:
        return await get_weather(lat,lon)
    except Exception as e:
        raise HTTPException(502,str(e))

@router.get("/route-predict")
async def route_predict(origin:str, destination:str):
    if origin not in KOLKATA_LOCATIONS or destination not in KOLKATA_LOCATIONS:
        raise HTTPException(400,"Please select valid Kolkata locations.")
    if origin == destination:
        raise HTTPException(400,"Origin and destination must be different.")

    try:
        start=KOLKATA_LOCATIONS[origin]
        end=KOLKATA_LOCATIONS[destination]
        route_data=await get_route(start,end)
        route=(route_data.get("routes") or [None])[0]
        if not route:
            raise RuntimeError("No route found.")

        summary=route.get("summary",{})
        distance_m=max(float(summary.get("lengthInMeters",0)),1)
        travel_time=max(float(summary.get("travelTimeInSeconds",0)),1)
        traffic_delay=max(float(summary.get("trafficDelayInSeconds",0)),0)
        current_speed=(distance_m/travel_time)*3.6
        free_time=max(travel_time-traffic_delay,1)
        free_flow_speed=(distance_m/free_time)*3.6

        weather=await get_weather(*end)
        level,prob,predicted_speed=predictor.predict(
            current_speed,
            max(free_flow_speed,current_speed),
            datetime.now().hour,
            weather.get("weather_impact",0),
        )

        points=[]
        for leg in route.get("legs",[]):
            points.extend(
                {"lat":p["latitude"],"lon":p["longitude"]}
                for p in leg.get("points",[])
                if "latitude" in p and "longitude" in p
            )

        return {
            "origin":origin,
            "destination":destination,
            "distance_km":round(distance_m/1000,2),
            "travel_time_min":round(travel_time/60,1),
            "traffic_delay_min":round(traffic_delay/60,1),
            "current_speed":round(current_speed,1),
            "free_flow_speed":round(free_flow_speed,1),
            "predicted_speed":predicted_speed,
            "congestion_level":level,
            "probability":prob,
            "weather":weather,
            "route_points":points,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502,str(e))
