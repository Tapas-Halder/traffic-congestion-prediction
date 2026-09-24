from fastapi import FastAPI

from database import engine, Base
from routes.traffic import router as traffic_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Traffic Congestion Prediction API",
    version="1.0.0"
)


app.include_router(traffic_router)


@app.get("/")
def root():

    return {
        "message": "Traffic Congestion Prediction API is running"
    }
