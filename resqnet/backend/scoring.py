"""
RESQNET Urgency Scoring & Spatial Duplicate Detection Engine
Formula: Urgency Score = (3 * children) + (2 * injured) + type_weight + minutes_waiting
"""
import math
from datetime import datetime

TYPE_WEIGHTS = {
    "Trapped / Structural Collapse": 15,
    "Medical Emergency": 12,
    "Flash Flood / Rising Water": 10,
    "Landslide": 10,
    "Fire / Hazard": 8,
    "Food / Water Shortage": 4,
    "Other": 2
}

def calculate_urgency_score(children_count: int, injured_count: int, emergency_type: str, created_at_iso: str, now_dt: datetime):
    created_dt = datetime.fromisoformat(created_at_iso)
    minutes_waiting = max(0, int((now_dt - created_dt).total_seconds() // 60))
    type_weight = TYPE_WEIGHTS.get(emergency_type, 5)
    score = (3 * int(children_count)) + (2 * int(injured_count)) + type_weight + minutes_waiting
    return {
        "urgency_score": score,
        "minutes_waiting": minutes_waiting,
        "type_weight": type_weight,
        "children_bonus": 3 * int(children_count),
        "injured_bonus": 2 * int(injured_count)
    }

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_m = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    return 2.0 * earth_radius_m * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
