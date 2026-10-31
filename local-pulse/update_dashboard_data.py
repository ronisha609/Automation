#!/usr/bin/env python3
"""Collect public local-condition data for the static commuter dashboard."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NWS_ALERTS = "https://api.weather.gov/alerts/active?area=NJ"
NWS_POINT = "https://api.weather.gov/points/40.2171,-74.7429"
INCIDENTS = "https://511nj.org/RSS511Service/RSS511Service.svc/rest/rss/RSSActiveIncidents"
CONSTRUCTION = "https://511nj.org/RSS511Service/RSS511Service.svc/rest/rss/RSSActiveConstruction"
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
USER_AGENT = "Local-Conditions-Monitor/1.0 github.com/ronisha609/Automation"


def fetch_bytes(url: str, accept: str = "application/json") -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_json(url: str) -> dict[str, Any]:
    return json.loads(fetch_bytes(url).decode("utf-8-sig"))


def text(node: ET.Element, name: str) -> str:
    child = node.find(name)
    return (child.text or "").strip() if child is not None else ""


def find_coordinate(node: ET.Element, endings: tuple[str, ...]) -> str:
    for child in node.iter():
        tag = child.tag.lower()
        if any(tag.endswith(ending) for ending in endings) and child.text:
            return child.text.strip()
    return ""


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def parse_511(payload: bytes, event_type: str) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    records: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        point = find_coordinate(item, ("point",))
        lat_raw = find_coordinate(item, ("lat", "latitude"))
        lon_raw = find_coordinate(item, ("long", "lon", "longitude"))
        if point and len(point.split()) >= 2:
            lat_raw, lon_raw = point.split()[:2]
        try:
            latitude, longitude = float(lat_raw), float(lon_raw)
        except (TypeError, ValueError):
            latitude = longitude = None
        title = clean_html(text(item, "title"))
        description = clean_html(text(item, "description"))
        records.append(
            {
                "type": event_type,
                "title": title or description or "Road event",
                "description": description or title,
                "published": text(item, "pubDate"),
                "link": text(item, "link") or text(item, "guid") or "https://511nj.org/",
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return records


def collect_weather() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    point = fetch_json(NWS_POINT)
    props = point.get("properties", {})
    hourly_url = props.get("forecastHourly")
    hourly = fetch_json(hourly_url) if hourly_url else {"properties": {"periods": []}}
    periods = hourly.get("properties", {}).get("periods", [])[:12]
    location = props.get("relativeLocation", {}).get("properties", {})
    weather = {
        "location": f"{location.get('city', 'Central New Jersey')}, {location.get('state', 'NJ')}",
        "periods": [
            {
                "startTime": period.get("startTime"),
                "temperature": period.get("temperature"),
                "temperatureUnit": period.get("temperatureUnit"),
                "windSpeed": period.get("windSpeed"),
                "windDirection": period.get("windDirection"),
                "shortForecast": period.get("shortForecast"),
                "probabilityOfPrecipitation": (
                    period.get("probabilityOfPrecipitation", {}) or {}
                ).get("value"),
                "icon": period.get("icon"),
            }
            for period in periods
        ],
    }
    alerts_payload = fetch_json(NWS_ALERTS)
    alerts: list[dict[str, Any]] = []
    for feature in alerts_payload.get("features", []):
        p = feature.get("properties", {})
        alerts.append(
            {
                "title": p.get("headline") or p.get("event") or "Weather alert",
                "event": p.get("event"),
                "severity": p.get("severity"),
                "urgency": p.get("urgency"),
                "area": p.get("areaDesc"),
                "description": clean_html(p.get("description") or ""),
                "instruction": clean_html(p.get("instruction") or ""),
                "sent": p.get("sent"),
                "expires": p.get("expires"),
                "url": p.get("web") or p.get("@id") or feature.get("id"),
                "geometry": feature.get("geometry"),
            }
        )
    return weather, alerts


def collect_news() -> list[dict[str, Any]]:
    query = '"New Jersey" (traffic OR closure OR flooding OR weather OR school OR outage OR event)'
    url = f"{GDELT}?{urlencode({'query': query, 'mode': 'artlist', 'maxrecords': 20, 'format': 'json', 'timespan': '24h', 'sort': 'datedesc'})}"
    payload = fetch_json(url)
    articles = payload.get("articles") or payload.get("items") or []
    return [
        {
            "title": article.get("title"),
            "url": article.get("url") or article.get("external_url"),
            "domain": article.get("domain") or article.get("source", {}).get("name"),
            "seenDate": article.get("seendate") or article.get("date_published"),
            "image": article.get("socialimage") or article.get("image"),
        }
        for article in articles
        if article.get("title") and (article.get("url") or article.get("external_url"))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/local_conditions.json"))
    args = parser.parse_args()
    statuses: dict[str, str] = {}
    output: dict[str, Any] = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "defaultLocation": {"label": "Central New Jersey", "latitude": 40.2171, "longitude": -74.7429},
        "weather": {"location": "Central New Jersey", "periods": []},
        "alerts": [],
        "traffic": [],
        "news": [],
        "statuses": statuses,
    }

    try:
        output["weather"], output["alerts"] = collect_weather()
        statuses["weather"] = "available"
    except Exception as exc:  # preserve partial collection
        statuses["weather"] = f"unavailable: {exc}"

    for name, url, kind in (
        ("incidents", INCIDENTS, "incident"),
        ("construction", CONSTRUCTION, "construction"),
    ):
        try:
            records = parse_511(fetch_bytes(url, "application/rss+xml, application/xml"), kind)
            output["traffic"].extend(records)
            statuses[name] = f"available: {len(records)} records"
        except Exception as exc:
            statuses[name] = f"unavailable: {exc}"

    try:
        output["news"] = collect_news()
        statuses["news"] = f"available: {len(output['news'])} records"
    except Exception as exc:
        statuses["news"] = f"unavailable: {exc}"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.output} with {len(output['traffic'])} road events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
