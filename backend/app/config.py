import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    tomtom_api_key: str = os.getenv("TOMTOM_API_KEY", "")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    city: str = os.getenv("CITY", "Kolkata")
    latitude: float = float(os.getenv("LATITUDE", "22.5726"))
    longitude: float = float(os.getenv("LONGITUDE", "88.3639"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "10"))

settings = Settings()
