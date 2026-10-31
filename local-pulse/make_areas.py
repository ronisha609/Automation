#!/usr/bin/env python3
"""Build data/areas.json: the areas that get a daily phone message.

New Jersey is covered county by county (centered on each county seat) with 511NJ traffic.
Major U.S. cities get weather and official alerts. To add a requested town, add one line
to EXTRA_AREAS below and run:  python make_areas.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# (county, county seat, latitude, longitude)
NJ_COUNTIES = [
    ("Atlantic", "Mays Landing", 39.452, -74.728), ("Bergen", "Hackensack", 40.886, -74.043),
    ("Burlington", "Mount Holly", 39.993, -74.788), ("Camden", "Camden", 39.926, -75.120),
    ("Cape May", "Cape May Court House", 39.083, -74.823), ("Cumberland", "Bridgeton", 39.427, -75.234),
    ("Essex", "Newark", 40.736, -74.172), ("Gloucester", "Woodbury", 39.838, -75.153),
    ("Hudson", "Jersey City", 40.728, -74.078), ("Hunterdon", "Flemington", 40.512, -74.859),
    ("Mercer", "Trenton", 40.217, -74.743), ("Middlesex", "New Brunswick", 40.486, -74.452),
    ("Monmouth", "Freehold", 40.260, -74.274), ("Morris", "Morristown", 40.797, -74.481),
    ("Ocean", "Toms River", 39.954, -74.198), ("Passaic", "Paterson", 40.917, -74.172),
    ("Salem", "Salem", 39.572, -75.467), ("Somerset", "Somerville", 40.574, -74.610),
    ("Sussex", "Newton", 41.058, -74.753), ("Union", "Elizabeth", 40.664, -74.211),
    ("Warren", "Belvidere", 40.830, -75.078),
]

# (city, state, latitude, longitude)
MAJOR_CITIES = [
    ("New York", "NY", 40.713, -74.006), ("Los Angeles", "CA", 34.052, -118.244),
    ("Chicago", "IL", 41.878, -87.630), ("Houston", "TX", 29.760, -95.370),
    ("Phoenix", "AZ", 33.448, -112.074), ("Philadelphia", "PA", 39.953, -75.165),
    ("San Antonio", "TX", 29.424, -98.494), ("San Diego", "CA", 32.716, -117.161),
    ("Dallas", "TX", 32.777, -96.797), ("Jacksonville", "FL", 30.332, -81.656),
    ("Austin", "TX", 30.267, -97.743), ("Fort Worth", "TX", 32.755, -97.331),
    ("San Jose", "CA", 37.338, -121.886), ("Columbus", "OH", 39.961, -82.999),
    ("Charlotte", "NC", 35.227, -80.843), ("Indianapolis", "IN", 39.768, -86.158),
    ("San Francisco", "CA", 37.775, -122.419), ("Seattle", "WA", 47.606, -122.332),
    ("Denver", "CO", 39.739, -104.990), ("Oklahoma City", "OK", 35.468, -97.516),
    ("Nashville", "TN", 36.163, -86.781), ("Washington", "DC", 38.907, -77.037),
    ("El Paso", "TX", 31.762, -106.485), ("Las Vegas", "NV", 36.170, -115.140),
    ("Boston", "MA", 42.360, -71.059), ("Detroit", "MI", 42.331, -83.046),
    ("Portland", "OR", 45.515, -122.679), ("Louisville", "KY", 38.253, -85.759),
    ("Memphis", "TN", 35.150, -90.049), ("Baltimore", "MD", 39.290, -76.612),
    ("Milwaukee", "WI", 43.039, -87.906), ("Albuquerque", "NM", 35.084, -106.650),
    ("Atlanta", "GA", 33.749, -84.388), ("Kansas City", "MO", 39.100, -94.578),
    ("Miami", "FL", 25.762, -80.192), ("New Orleans", "LA", 29.951, -90.072),
    ("Minneapolis", "MN", 44.978, -93.265), ("Tampa", "FL", 27.951, -82.457),
    ("Raleigh", "NC", 35.780, -78.638), ("Richmond", "VA", 37.541, -77.436),
    ("Virginia Beach", "VA", 36.853, -75.978), ("Pittsburgh", "PA", 40.441, -79.996),
    ("Cleveland", "OH", 41.499, -81.694), ("St. Louis", "MO", 38.627, -90.199),
    ("Salt Lake City", "UT", 40.761, -111.891), ("Honolulu", "HI", 21.307, -157.858),
    ("Anchorage", "AK", 61.218, -149.900),
]

# Approved town requests: (town, state, latitude, longitude)
EXTRA_AREAS: list[tuple[str, str, float, float]] = []


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build() -> list[dict]:
    areas = []
    for county, seat, lat, lon in NJ_COUNTIES:
        areas.append({
            "id": f"nj-{slug(county)}", "label": f"{county} County, NJ", "center": f"{seat}, NJ",
            "state": "NJ", "lat": lat, "lon": lon, "radiusMiles": 15, "traffic": "511nj",
            "topic": f"local-pulse-nj-{slug(county)}",
        })
    for city, state, lat, lon in MAJOR_CITIES + EXTRA_AREAS:
        areas.append({
            "id": f"{state.lower()}-{slug(city)}", "label": f"{city}, {state}", "center": f"{city}, {state}",
            "state": state, "lat": lat, "lon": lon, "radiusMiles": 15,
            "traffic": "511nj" if state == "NJ" else None,
            "topic": f"local-pulse-{state.lower()}-{slug(city)}",
        })
    return areas


if __name__ == "__main__":
    out = Path(__file__).parent / "data" / "areas.json"
    areas = build()
    out.write_text(json.dumps({"areas": areas}, indent=1), encoding="utf-8")
    print(f"Wrote {len(areas)} areas to {out}")
