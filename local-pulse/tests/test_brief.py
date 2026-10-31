import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from brief import (
    build_facts,
    facts_fingerprint,
    impact_flags,
    local_alerts,
    nearby_roads,
    rules_brief,
    write_journal,
)
from journal import load_entries, summarize


def snapshot(rain=10, low_temp=50, alerts=None, traffic=None):
    return {
        "weather": {"periods": [
            {"startTime": "2026-10-31T07:00:00-04:00", "temperature": low_temp, "temperatureUnit": "F",
             "shortForecast": "Cloudy", "probabilityOfPrecipitation": 5},
            {"startTime": "2026-10-31T17:00:00-04:00", "temperature": 61, "temperatureUnit": "F",
             "shortForecast": "Rain", "probabilityOfPrecipitation": rain},
        ]},
        "alerts": alerts or [],
        "traffic": traffic or [],
        "news": [{"title": "Parade closes Main Street tonight"}],
    }


CRASH_NEAR = {"type": "incident", "title": "I-295 northbound at Exit 60", "description": "Crash, right lane closed",
              "latitude": 40.25, "longitude": -74.70}
WORK_NEAR = {"type": "construction", "title": "Route 1 at Alexander Rd", "description": "Lane shift",
             "latitude": 40.30, "longitude": -74.68}
CRASH_FAR = {"type": "incident", "title": "Garden State Pkwy Exit 1", "description": "Crash",
             "latitude": 38.97, "longitude": -74.88}


class BriefTests(unittest.TestCase):
    def test_roads_filtered_by_distance_and_ranked(self):
        roads = nearby_roads(snapshot(traffic=[WORK_NEAR, CRASH_FAR, CRASH_NEAR, CRASH_NEAR]))
        self.assertEqual([r["title"] for r in roads], [CRASH_NEAR["title"], WORK_NEAR["title"]])
        self.assertEqual(roads[0]["label"], "crash or incident")

    def test_only_alerts_for_local_counties(self):
        alerts = [{"event": "Flood Warning", "area": "Mercer; Burlington"},
                  {"event": "Coastal Flood Advisory", "area": "Cape May"}]
        self.assertEqual([a["event"] for a in local_alerts(snapshot(alerts=alerts))], ["Flood Warning"])

    def test_rules_brief_mentions_crash_and_rain(self):
        facts = build_facts(snapshot(rain=70, traffic=[CRASH_NEAR]), today=datetime(2026, 11, 3))
        text = rules_brief(facts)
        self.assertTrue(text.startswith("Good morning"))
        self.assertIn("I-295", text)
        self.assertIn("umbrella", text)
        self.assertLessEqual(len(text), 600)

    def test_quiet_day(self):
        facts = build_facts(snapshot(), today=datetime(2026, 11, 3))
        self.assertIn("look clear", rules_brief(facts))
        self.assertEqual(impact_flags(facts), ["quiet day"])

    def test_flags(self):
        facts = build_facts(snapshot(rain=60, low_temp=33, traffic=[CRASH_NEAR],
                                     alerts=[{"event": "Flood Watch", "area": "Mercer"}]),
                            today=datetime(2026, 11, 3))
        flags = impact_flags(facts)
        for flag in ("crash or closure", "rain", "cold or frost", "weather alert", "flooding"):
            self.assertIn(flag, flags)

    def test_fingerprint_ignores_headlines(self):
        a = build_facts(snapshot(), today=datetime(2026, 11, 3))
        b = dict(a, headlines=["Something else"])
        self.assertEqual(facts_fingerprint(a), facts_fingerprint(b))

    def test_journal_round_trip(self):
        facts = build_facts(snapshot(traffic=[CRASH_NEAR]), today=datetime(2026, 11, 3))
        brief = {"generatedAt": "2026-11-03T11:15:00+00:00", "text": rules_brief(facts), "source": "rules", "facts": facts}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_journal(brief, folder, "2026-11-03")
            entries = load_entries(folder)
            self.assertEqual(len(entries), 1)
            summary = summarize(entries, "2026-11-01", 90)
            self.assertEqual(summary["briefsSent"], 1)
            self.assertEqual(summary["daysWith"]["crash or closure"], 1)
            self.assertEqual(json.loads((folder / "2026-11-03.json").read_text())["writtenBy"], "built-in rules")


class AreaTests(unittest.TestCase):
    def test_area_without_traffic_skips_road_line(self):
        area = {"label": "Richmond, VA", "lat": 37.541, "lon": -77.436, "radiusMiles": 15,
                "traffic": None, "counties": None}
        facts = build_facts(snapshot(traffic=[CRASH_NEAR]), today=datetime(2026, 11, 3), area=area)
        text = rules_brief(facts)
        self.assertTrue(text.startswith("Good morning, Richmond, VA."))
        self.assertNotIn("Roads", text)
        self.assertNotIn("I-295", text)

    def test_area_alerts_not_county_filtered(self):
        area = {"label": "Richmond, VA", "lat": 37.541, "lon": -77.436, "traffic": None, "counties": None}
        facts = build_facts(snapshot(alerts=[{"event": "Wind Advisory", "area": "Henrico"}]),
                            today=datetime(2026, 11, 3), area=area)
        self.assertEqual([a["event"] for a in facts["weatherAlerts"]], ["Wind Advisory"])

    def test_areas_file_is_valid(self):
        from make_areas import build
        areas = build()
        self.assertEqual(len({a["topic"] for a in areas}), len(areas))
        self.assertEqual(sum(1 for a in areas if a["state"] == "NJ"), 21)
        for a in areas:
            self.assertTrue(-180 < a["lon"] < -60 and 18 < a["lat"] < 72, a["label"])

    def test_request_merge_dedupes(self):
        from requests_log import merge
        merged = merge([], [{"id": "a", "time": 2, "message": "Smithfield, VA"},
                            {"id": "a", "time": 2, "message": "Smithfield, VA"},
                            {"id": "b", "time": 1, "message": "Ewing, NJ"}])
        self.assertEqual([r["town"] for r in merged], ["Ewing, NJ", "Smithfield, VA"])


if __name__ == "__main__":
    unittest.main()
