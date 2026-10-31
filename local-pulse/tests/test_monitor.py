import unittest
from datetime import datetime, timezone

from monitor import (
    deduplicate,
    demo_payloads,
    earthquake_risk,
    map_nws_risk,
    parse_cisa,
    parse_nws,
    parse_usgs,
    sort_items,
)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        self.payloads = demo_payloads(self.now)

    def test_nws_immediate_severe_alert_is_high(self):
        items = parse_nws(self.payloads["nws"])
        self.assertEqual(items[0].risk, "High")
        self.assertEqual(map_nws_risk("Severe", "Immediate"), "High")

    def test_usgs_filters_by_radius(self):
        near = parse_usgs(
            self.payloads["usgs"], latitude=40.2171, longitude=-74.7429, radius_km=300
        )
        far = parse_usgs(
            self.payloads["usgs"], latitude=34.0522, longitude=-118.2437, radius_km=50
        )
        self.assertEqual(len(near), 1)
        self.assertEqual(far, [])
        self.assertEqual(earthquake_risk(3.6, 20, "", False), "Moderate")

    def test_cisa_recent_ransomware_item_is_high(self):
        items = parse_cisa(self.payloads["cisa"], lookback_days=14, now=self.now)
        self.assertEqual(items[0].risk, "High")
        self.assertIn("CVE-DEMO-0001", items[0].title)

    def test_deduplication_and_risk_sorting(self):
        items = parse_nws(self.payloads["nws"])
        quake = parse_usgs(
            self.payloads["usgs"], latitude=40.2171, longitude=-74.7429, radius_km=300
        )
        ranked = sort_items(deduplicate(items + items + quake))
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].risk, "High")


if __name__ == "__main__":
    unittest.main()
