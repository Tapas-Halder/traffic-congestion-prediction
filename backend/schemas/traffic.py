from datetime import datetime
from pydantic import BaseModel,Field
class PredictionRequest(BaseModel):
 latitude:float=Field(...,ge=-90,le=90); longitude:float=Field(...,ge=-180,le=180)
 speed:float=Field(...,ge=0); free_flow_speed:float=Field(40,gt=0)
 hour:int|None=Field(None,ge=0,le=23); weather:float=Field(0,ge=0,le=100)
class PredictionResponse(BaseModel):
 congestion_level:str; probability:float; predicted_speed:float
class TrafficResponse(BaseModel):
 timestamp:datetime; latitude:float; longitude:float; speed:float; free_flow_speed:float; congestion_level:str; confidence:float
