from datetime import datetime
from sqlalchemy import DateTime,Float,Integer,String
from sqlalchemy.orm import Mapped,mapped_column
from database import Base
class TrafficRecord(Base):
 __tablename__="traffic_records"
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 timestamp:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
 latitude:Mapped[float]=mapped_column(Float); longitude:Mapped[float]=mapped_column(Float)
 speed:Mapped[float]=mapped_column(Float); free_flow_speed:Mapped[float]=mapped_column(Float)
 confidence:Mapped[float]=mapped_column(Float,default=0); congestion_level:Mapped[str]=mapped_column(String(20))
