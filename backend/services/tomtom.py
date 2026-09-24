import httpx
from config import TOMTOM_API_KEY
URL="https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
async def get_traffic(lat,lon):
 if not TOMTOM_API_KEY: raise RuntimeError("TOMTOM_API_KEY is not configured")
 async with httpx.AsyncClient(timeout=10) as c:
  r=await c.get(URL,params={"point":f"{lat},{lon}","key":TOMTOM_API_KEY}); r.raise_for_status(); return r.json()
