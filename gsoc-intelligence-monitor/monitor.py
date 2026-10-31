#!/usr/bin/env python3
"""Automated GSOC intelligence monitor using official public data sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NWS_ALERTS = "https://api.weather.gov/alerts/active"
USGS_EARTHQUAKES = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
)
CISA_KEV = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)

RISK_ORDER = {"High": 3, "Moderate": 2, "Low": 1, "Information": 0}


@dataclass(frozen=True)
class IntelItem:
    source: str
    category: str
    title: str
    risk: str
    published: str
    summary: str
    url: str
    indicators: tuple[str, ...]
    recommended_action: str

    @property
    def fingerprint(self) -> str:
        normalized = re.sub(r"\W+", " ", f"{self.source} {self.title} {self.url}").lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


DEFAULT_CONFIG: dict[str, Any] = {
    "location_label": "Central New Jersey",
    "latitude": 40.2171,
    "longitude": -74.7429,
    "earthquake_radius_km": 300,
    "cisa_lookback_days": 14,
    "max_items": 12,
    "request_timeout_seconds": 15,
    "user_agent": "GSOC-Intelligence-Monitor/1.0 contact@example.com",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    value = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_config(path: Path | None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path:
        with path.open("r", encoding="utf-8") as handle:
            config.update(json.load(handle))

    env_map = {
        "MONITOR_LOCATION": "location_label",
        "MONITOR_LAT": "latitude",
        "MONITOR_LON": "longitude",
        "MONITOR_RADIUS_KM": "earthquake_radius_km",
    }
    for env_name, key in env_map.items():
        if env_name in os.environ:
            config[key] = os.environ[env_name]

    for key in ("latitude", "longitude", "earthquake_radius_km"):
        config[key] = float(config[key])
    for key in ("cisa_lookback_days", "max_items", "request_timeout_seconds"):
        config[key] = int(config[key])
    return config


def fetch_json(url: str, *, user_agent: str, timeout: int) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": user_agent,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def map_nws_risk(severity: str, urgency: str) -> str:
    severity = severity.lower()
    urgency = urgency.lower()
    if severity in {"extreme", "severe"} or urgency == "immediate":
        return "High"
    if severity == "moderate" or urgency in {"expected", "future"}:
        return "Moderate"
    return "Low"


def parse_nws(payload: dict[str, Any]) -> list[IntelItem]:
    items: list[IntelItem] = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        event = props.get("event") or "Weather alert"
        severity = props.get("severity") or "Unknown"
        urgency = props.get("urgency") or "Unknown"
        area = props.get("areaDesc") or "Area not specified"
        items.append(
            IntelItem(
                source="National Weather Service",
                category="Weather",
                title=props.get("headline") or event,
                risk=map_nws_risk(severity, urgency),
                published=props.get("sent") or props.get("effective") or "",
                summary=f"{event} affecting {area}. Severity: {severity}; urgency: {urgency}.",
                url=props.get("web") or props.get("@id") or feature.get("id", ""),
                indicators=(f"Severity: {severity}", f"Urgency: {urgency}", f"Area: {area}"),
                recommended_action=(
                    "Verify the alert, review timing and affected areas, and adjust movement plans."
                ),
            )
        )
    return items


def earthquake_risk(magnitude: float, distance_km: float, alert: str, tsunami: bool) -> str:
    if tsunami or alert in {"red", "orange"} or magnitude >= 5.0:
        return "High"
    if magnitude >= 3.5 or distance_km <= 100:
        return "Moderate"
    return "Low"


def parse_usgs(
    payload: dict[str, Any], *, latitude: float, longitude: float, radius_km: float
) -> list[IntelItem]:
    items: list[IntelItem] = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        if len(coordinates) < 2:
            continue
        event_lon, event_lat = float(coordinates[0]), float(coordinates[1])
        distance = haversine_km(latitude, longitude, event_lat, event_lon)
        if distance > radius_km:
            continue
        magnitude = float(props.get("mag") or 0)
        alert = str(props.get("alert") or "").lower()
        tsunami = bool(props.get("tsunami"))
        event_time = datetime.fromtimestamp(
            float(props.get("time", 0)) / 1000, tz=timezone.utc
        ).isoformat()
        place = props.get("place") or "Location not specified"
        items.append(
            IntelItem(
                source="U.S. Geological Survey",
                category="Seismic",
                title=props.get("title") or f"M {magnitude:.1f} earthquake near {place}",
                risk=earthquake_risk(magnitude, distance, alert, tsunami),
                published=event_time,
                summary=(
                    f"Magnitude {magnitude:.1f} earthquake approximately {distance:.0f} km "
                    f"from the monitored location."
                ),
                url=props.get("url") or "",
                indicators=(
                    f"Magnitude: {magnitude:.1f}",
                    f"Distance: {distance:.0f} km",
                    f"Tsunami flag: {'Yes' if tsunami else 'No'}",
                ),
                recommended_action=(
                    "Verify USGS impact products and monitor local emergency guidance if felt locally."
                ),
            )
        )
    return items


def parse_cisa(payload: dict[str, Any], *, lookback_days: int, now: datetime) -> list[IntelItem]:
    cutoff = now.date() - timedelta(days=lookback_days)
    items: list[IntelItem] = []
    for vuln in payload.get("vulnerabilities", []):
        added = parse_datetime(vuln.get("dateAdded"))
        if added.date() < cutoff:
            continue
        ransomware = str(vuln.get("knownRansomwareCampaignUse", "Unknown"))
        risk = "High" if ransomware.lower() == "known" else "Moderate"
        cve = vuln.get("cveID") or "CVE not listed"
        vendor = vuln.get("vendorProject") or "Unknown vendor"
        product = vuln.get("product") or "Unknown product"
        action = vuln.get("requiredAction") or "Review CISA remediation guidance."
        items.append(
            IntelItem(
                source="CISA Known Exploited Vulnerabilities",
                category="Cyber",
                title=f"{cve}: {vuln.get('vulnerabilityName') or f'{vendor} {product} vulnerability'}",
                risk=risk,
                published=vuln.get("dateAdded") or "",
                summary=(
                    f"CISA added an actively exploited vulnerability affecting {vendor} {product}. "
                    f"Known ransomware use: {ransomware}."
                ),
                url=f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search_api_fulltext={cve}",
                indicators=(
                    f"CVE: {cve}",
                    f"Vendor/Product: {vendor} {product}",
                    f"Federal due date: {vuln.get('dueDate') or 'Not listed'}",
                ),
                recommended_action=action,
            )
        )
    return items


def deduplicate(items: Iterable[IntelItem]) -> list[IntelItem]:
    unique: dict[str, IntelItem] = {}
    for item in items:
        unique.setdefault(item.fingerprint, item)
    return list(unique.values())


def sort_items(items: Iterable[IntelItem]) -> list[IntelItem]:
    return sorted(
        items,
        key=lambda item: (RISK_ORDER.get(item.risk, 0), parse_datetime(item.published)),
        reverse=True,
    )


def generate_brief(
    items: list[IntelItem],
    *,
    location_label: str,
    generated_at: datetime,
    source_status: dict[str, str],
    demo: bool,
) -> str:
    counts = {risk: sum(item.risk == risk for item in items) for risk in RISK_ORDER}
    highest = next((risk for risk in ("High", "Moderate", "Low") if counts[risk]), "No active items")
    mode_note = " **Demonstration data is active.**" if demo else ""
    lines = [
        f"# GSOC Intelligence Brief — {location_label}",
        "",
        f"**Generated:** {generated_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Overall posture:** {highest}  ",
        f"**Items reviewed:** {len(items)}{mode_note}",
        "",
        "## Executive Summary",
        "",
        (
            f"The automated collection identified **{counts['High']} high**, "
            f"**{counts['Moderate']} moderate**, and **{counts['Low']} low** priority items. "
            "Analyst review is required before operational decisions or escalation."
        ),
        "",
        "## Priority Watch Items",
        "",
    ]
    if not items:
        lines.append("No matching alerts were returned by the configured sources.")
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"### {index}. [{item.risk}] {item.title}",
                "",
                f"- **Source:** {item.source}",
                f"- **Category:** {item.category}",
                f"- **Published:** {item.published or 'Not provided'}",
                f"- **Assessment:** {item.summary}",
                f"- **Indicators:** {'; '.join(item.indicators)}",
                f"- **Action:** {item.recommended_action}",
                f"- **Official record:** {item.url or 'Not provided'}",
                "",
            ]
        )
    lines.extend(["## Collection Status", ""])
    for source, status in source_status.items():
        lines.append(f"- **{source}:** {status}")
    lines.extend(
        [
            "",
            "## Analytic Note",
            "",
            (
                "This product automates collection and first-pass prioritization. It does not replace "
                "source verification, local context, or analyst judgment. Confirm critical information "
                "through the linked official source before acting."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def demo_payloads(now: datetime) -> dict[str, dict[str, Any]]:
    """Schema-faithful fictional records for offline validation."""
    return {
        "nws": {
            "features": [
                {
                    "id": "https://api.weather.gov/alerts/demo-weather",
                    "properties": {
                        "event": "Severe Thunderstorm Warning",
                        "headline": "DEMO: Severe Thunderstorm Warning",
                        "severity": "Severe",
                        "urgency": "Immediate",
                        "areaDesc": "Demo County, New Jersey",
                        "sent": now.isoformat(),
                        "description": "Demonstration record for parser validation.",
                    },
                }
            ]
        },
        "usgs": {
            "features": [
                {
                    "id": "demo-quake",
                    "properties": {
                        "mag": 3.6,
                        "place": "Demo location",
                        "time": int(now.timestamp() * 1000),
                        "url": "https://earthquake.usgs.gov/",
                        "title": "DEMO: M 3.6 earthquake",
                        "alert": None,
                        "tsunami": 0,
                    },
                    "geometry": {"coordinates": [-74.6, 40.3, 5.0]},
                }
            ]
        },
        "cisa": {
            "vulnerabilities": [
                {
                    "cveID": "CVE-DEMO-0001",
                    "vendorProject": "Demo Vendor",
                    "product": "Demo Product",
                    "vulnerabilityName": "Demonstration vulnerability",
                    "dateAdded": now.date().isoformat(),
                    "dueDate": (now.date() + timedelta(days=14)).isoformat(),
                    "requiredAction": "Validate exposure and apply vendor mitigations.",
                    "knownRansomwareCampaignUse": "Known",
                }
            ]
        },
    }


def collect(config: dict[str, Any], *, demo: bool) -> tuple[list[IntelItem], dict[str, str]]:
    now = utc_now()
    status: dict[str, str] = {}
    items: list[IntelItem] = []
    payloads = demo_payloads(now) if demo else {}

    sources = [
        (
            "National Weather Service",
            lambda: payloads["nws"]
            if demo
            else fetch_json(
                f"{NWS_ALERTS}?{urlencode({'point': '{},{}'.format(config['latitude'], config['longitude'])})}",
                user_agent=config["user_agent"],
                timeout=config["request_timeout_seconds"],
            ),
            lambda payload: parse_nws(payload),
        ),
        (
            "U.S. Geological Survey",
            lambda: payloads["usgs"]
            if demo
            else fetch_json(
                USGS_EARTHQUAKES,
                user_agent=config["user_agent"],
                timeout=config["request_timeout_seconds"],
            ),
            lambda payload: parse_usgs(
                payload,
                latitude=config["latitude"],
                longitude=config["longitude"],
                radius_km=config["earthquake_radius_km"],
            ),
        ),
        (
            "CISA KEV",
            lambda: payloads["cisa"]
            if demo
            else fetch_json(
                CISA_KEV,
                user_agent=config["user_agent"],
                timeout=config["request_timeout_seconds"],
            ),
            lambda payload: parse_cisa(
                payload, lookback_days=config["cisa_lookback_days"], now=now
            ),
        ),
    ]

    for source_name, loader, parser in sources:
        try:
            parsed = parser(loader())
            items.extend(parsed)
            status[source_name] = f"Collected successfully; {len(parsed)} matching item(s)."
        except RuntimeError as exc:
            status[source_name] = f"Collection failed: {exc}"

    ranked = sort_items(deduplicate(items))
    return ranked[: config["max_items"]], status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Path to a JSON configuration file")
    parser.add_argument("--output", type=Path, default=Path("output/brief.md"))
    parser.add_argument("--json-output", type=Path, help="Optional normalized JSON output")
    parser.add_argument("--demo", action="store_true", help="Use labeled fictional records")
    args = parser.parse_args()

    config = load_config(args.config)
    items, source_status = collect(config, demo=args.demo)
    generated_at = utc_now()
    brief = generate_brief(
        items,
        location_label=config["location_label"],
        generated_at=generated_at,
        source_status=source_status,
        demo=args.demo,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(brief, encoding="utf-8")

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps([asdict(item) for item in items], indent=2), encoding="utf-8"
        )

    print(f"Wrote {args.output} with {len(items)} prioritized item(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
