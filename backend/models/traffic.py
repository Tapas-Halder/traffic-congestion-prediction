from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime

from database import Base


class TrafficData(Base):

    __tablename__ = "traffic_data"

    id = Column(Integer, primary_key=True, index=True)

    location = Column(String, nullable=False)

    vehicle_count = Column(Integer)

    average_speed = Column(Float)

    occupancy = Column(Float)

    temperature = Column(Float)

    rainfall = Column(Float)

    congestion_level = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
