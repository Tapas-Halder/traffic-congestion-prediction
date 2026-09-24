import httpx
from config import OPENWEATHER_API_KEY

URL="https://api.openweathermap.org/data/2.5/weather"

async def get_weather(lat,lon):
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY is not configured")
    async with httpx.AsyncClient(timeout=10) as client:
        response=await client.get(
            URL,
            params={
                "lat":lat,
                "lon":lon,
                "appid":OPENWEATHER_API_KEY,
                "units":"metric",
            },
        )
        response.raise_for_status()
        data=response.json()

    main=data.get("main",{})
    clouds=data.get("clouds",{}).get("all",0)
    rain_1h=data.get("rain",{}).get("1h",0)
    snow_1h=data.get("snow",{}).get("1h",0)

    impact=min(100, round(max(clouds, rain_1h*25, snow_1h*25)))
    return {
        "temperature":main.get("temp"),
        "humidity":main.get("humidity"),
        "description":(data.get("weather") or [{}])[0].get("description"),
        "clouds":clouds,
        "rain_1h":rain_1h,
        "snow_1h":snow_1h,
        "weather_impact":impact,
    }
