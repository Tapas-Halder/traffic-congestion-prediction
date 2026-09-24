from collections import defaultdict,deque
from datetime import datetime,timezone

_HISTORY=defaultdict(lambda:deque(maxlen=24))

def key(origin,destination):
    return f"{origin}__{destination}"

def add_snapshot(origin,destination,data):
    _HISTORY[key(origin,destination)].append({
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "current_speed":float(data["current_speed"]),
        "congestion_level":data["congestion_level"],
        "traffic_delay_min":float(data["traffic_delay_min"]),
        "predicted_speed":float(data["predicted_speed"]),
    })

def get_snapshots(origin,destination):
    return list(_HISTORY[key(origin,destination)])
