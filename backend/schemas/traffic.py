from pydantic import BaseModel


class TrafficCreate(BaseModel):

    location: str

    vehicle_count: int

    average_speed: float

    occupancy: float

    temperature: float

    rainfall: float


class TrafficResponse(BaseModel):

    id: int
    location: str
    vehicle_count: int
    average_speed: float
    occupancy: float
    temperature: float
    rainfall: float
    congestion_level: str

    class Config:
        from_attributes = True
