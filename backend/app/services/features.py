from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def build_prediction_features(payload: dict[str, Any]) -> dict[str, float]:
    """Convert TomTom + OpenWeather payload into the ML feature contract.

    Hour and weekday are computed in Kolkata local time to match ML training.
    """
    traffic = payload.get("traffic", {}).get("flowSegmentData", {})
    weather = payload.get("weather", {})
    rain = weather.get("rain", {}) or {}

    current_speed = float(traffic.get("currentSpeed", 0.0))
    free_flow_speed = float(traffic.get("freeFlowSpeed", 0.0))
    confidence = float(traffic.get("confidence", 0.0))
    now = datetime.fromisoformat(payload["collected_at"].replace("Z", "+00:00"))
    kolkata_now = now.astimezone(ZoneInfo("Asia/Kolkata"))

    return {
        "current_speed": current_speed,
        "free_flow_speed": free_flow_speed,
        "speed_ratio": current_speed / free_flow_speed if free_flow_speed else 0.0,
        "traffic_confidence": confidence,
        "temperature": float(weather.get("main", {}).get("temp", 0.0)),
        "humidity": float(weather.get("main", {}).get("humidity", 0.0)),
        "rain_1h": float(rain.get("1h", 0.0)),
        "hour": float(kolkata_now.hour),
        "day_of_week": float(kolkata_now.weekday()),
    }
