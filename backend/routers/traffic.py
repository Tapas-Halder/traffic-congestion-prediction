from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.traffic import TrafficData
from schemas.traffic import TrafficCreate


router = APIRouter(
    prefix="/traffic",
    tags=["Traffic"]
)


@router.post("/")
def create_traffic(
    data: TrafficCreate,
    db: Session = Depends(get_db)
):

    traffic = TrafficData(
        location=data.location,
        vehicle_count=data.vehicle_count,
        average_speed=data.average_speed,
        occupancy=data.occupancy,
        temperature=data.temperature,
        rainfall=data.rainfall,
        congestion_level="Unknown"
    )

    db.add(traffic)
    db.commit()
    db.refresh(traffic)

    return traffic
