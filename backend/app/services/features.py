"""Map real API measurements to the model's validated feature schema."""
from datetime import datetime, timezone
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo


def _number(value: Any, name: str, *, required: bool = False) -> float | None:
    if value is None or value == "":
        if required:
            raise ValueError(f"Missing required traffic value: {name}")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid numeric value: {name}") from exc
    if not isfinite(number):
        raise ValueError(f"Non-finite value: {name}")
    return number


def build_prediction_features(payload: dict[str, Any]) -> dict[str, float | None]:
    traffic = (payload.get("traffic") or {}).get("flowSegmentData") or {}
    weather = payload.get("weather") or {}
    main = weather.get("main") or {}
    rain = weather.get("rain") or {}
    current = _number(traffic.get("currentSpeed"), "currentSpeed", required=True)
    free = _number(traffic.get("freeFlowSpeed"), "freeFlowSpeed", required=True)
    if current < 0 or free <= 0:
        raise ValueError("Traffic speeds must be nonnegative and free-flow speed positive")
    confidence = _number(traffic.get("confidence"), "confidence")
    humidity = _number(main.get("humidity"), "humidity")
    rainfall = _number(rain.get("1h", 0.0), "rain_1h")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("Traffic confidence outside 0..1")
    if humidity is not None and not 0 <= humidity <= 100:
        raise ValueError("Humidity outside 0..100")
    if rainfall is not None and rainfall < 0:
        raise ValueError("Rainfall cannot be negative")
    observed = datetime.fromisoformat(payload["collected_at"].replace("Z", "+00:00"))
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    local = observed.astimezone(ZoneInfo("Asia/Kolkata"))
    return {
        "current_speed": current, "free_flow_speed": free,
        "speed_ratio": current / free, "traffic_confidence": confidence,
        "temperature": _number(main.get("temp"), "temperature"),
        "humidity": humidity, "rain_1h": rainfall,
        "hour": float(local.hour), "day_of_week": float(local.weekday()),
    }
