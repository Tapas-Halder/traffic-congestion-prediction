import httpx
from config import OPENWEATHER_API_KEY
URL="https://api.openweathermap.org/data/2.5/weather"
async def get_weather(lat,lon):
 if not OPENWEATHER_API_KEY: raise RuntimeError("OPENWEATHER_API_KEY is not configured")
 async with httpx.AsyncClient(timeout=10) as c:
  r=await c.get(URL,params={"lat":lat,"lon":lon,"appid":OPENWEATHER_API_KEY,"units":"metric"}); r.raise_for_status(); return r.json()
