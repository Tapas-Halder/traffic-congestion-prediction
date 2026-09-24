from datetime import datetime
from fastapi import APIRouter,HTTPException
from schemas.traffic import PredictionRequest,PredictionResponse
from services.predictor import predictor
from services.tomtom import get_traffic
from services.weather import get_weather
from config import DEFAULT_LAT,DEFAULT_LON
router=APIRouter(prefix="/api",tags=["traffic"])
@router.get("/health")
def health(): return {"status":"ok"}
@router.post("/predict",response_model=PredictionResponse)
def predict(p:PredictionRequest):
 level,prob,speed=predictor.predict(p.speed,p.free_flow_speed,p.hour if p.hour is not None else datetime.now().hour,p.weather)
 return {"congestion_level":level,"probability":prob,"predicted_speed":speed}
@router.get("/live")
async def live(lat:float=DEFAULT_LAT,lon:float=DEFAULT_LON):
 try:
  d=(await get_traffic(lat,lon)).get("flowSegmentData",{})
  return {"latitude":lat,"longitude":lon,"current_speed":d.get("currentSpeed"),"free_flow_speed":d.get("freeFlowSpeed"),"confidence":d.get("confidence"),"road_closure":d.get("roadClosure",False)}
 except Exception as e: raise HTTPException(502,str(e))
@router.get("/weather")
async def weather(lat:float=DEFAULT_LAT,lon:float=DEFAULT_LON):
 try: return await get_weather(lat,lon)
 except Exception as e: raise HTTPException(502,str(e))
