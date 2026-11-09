import unittest
from datetime import datetime, timezone, timedelta
from backend.services.scoring import calculate_urgency_score, haversine_distance_meters

class TestResqNetAlgorithms(unittest.TestCase):

    def test_urgency_formula_calculation(self):
        now = datetime.now(timezone.utc)
        ten_mins_ago = (now - timedelta(minutes=10)).isoformat()
        # 2 children (2*3=6) + 3 injured (3*2=6) + Trapped (15) + 10 mins = 37
        res = calculate_urgency_score(
            children_count=2,
            injured_count=3,
            emergency_type="Trapped / Structural Collapse",
            created_at_iso=ten_mins_ago,
            now_dt=now
        )
        self.assertEqual(res["urgency_score"], 37)

    def test_duplicate_detection_radius(self):
        # Two points ~25 meters apart should be within 50m duplicate threshold
        d = haversine_distance_meters(13.1830, 74.9340, 13.1832, 74.9341)
        self.assertLess(d, 50.0)

if __name__ == "__main__":
    unittest.main()
