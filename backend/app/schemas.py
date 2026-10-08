from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float
    longitude: float


class PredictionRequest(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class PredictionResponse(BaseModel):
    city: str
    location: Location
    prediction: str
    confidence: float | None = None
    source: str
    collected_at: str
