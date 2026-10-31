#!/usr/bin/env python3
"""Write and send the morning message for every area in data/areas.json.

Each area gets its own forecast and official alerts from the National Weather Service.
New Jersey areas also get nearby 511NJ crashes and construction from the shared snapshot.
Messages are written by the built-in rules, so this costs nothing to run.

Usage:
    python area_briefs.py                 # write data/area_briefs.json
    python area_briefs.py --send          # also push each message to its ntfy topic
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brief import build_facts, impact_flags, rules_brief, send_ntfy
from update_dashboard_data import clean_html as clean_html_text, fetch_json

SEND_PAUSE_SECONDS = 6   # stay well inside ntfy.sh's free rate limits
NWS_PAUSE_SECONDS = 0.5  # be polite to the weather service


def area_weather(lat: float, lon: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    point = fetch_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
    hourly_url = point.get("properties", {}).get("forecastHourly")
    periods = []
    if hourly_url:
        for p in fetch_json(hourly_url).get("properties", {}).get("periods", [])[:12]:
            periods.append({
                "startTime": p.get("startTime"),
                "temperature": p.get("temperature"),
                "temperatureUnit": p.get("temperatureUnit"),
                "shortForecast": p.get("shortForecast"),
                "probabilityOfPrecipitation": (p.get("probabilityOfPrecipitation") or {}).get("value"),
            })
    alerts = []
    for feature in fetch_json(f"https://api.weather.gov/alerts/active?point={lat:.4f},{lon:.4f}").get("features", []):
        p = feature.get("properties", {})
        alerts.append({
            "event": p.get("event"), "title": p.get("headline") or p.get("event"),
            "severity": p.get("severity"), "area": p.get("areaDesc"),
            "instruction": clean_html_text(p.get("instruction") or ""),
        })
    return periods, alerts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--areas", type=Path, default=Path("data/areas.json"))
    parser.add_argument("--snapshot", type=Path, default=Path("data/local_conditions.json"))
    parser.add_argument("--output", type=Path, default=Path("data/area_briefs.json"))
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    areas = json.loads(args.areas.read_text(encoding="utf-8"))["areas"]
    shared = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot.exists() else {}
    results: dict[str, Any] = {}
    sent = failed = 0

    for area in areas:
        try:
            periods, alerts = area_weather(area["lat"], area["lon"])
        except Exception as exc:
            results[area["id"]] = {"label": area["label"], "error": f"weather unavailable: {exc}"}
            print(f"[skip] {area['label']}: {exc}")
            continue
        snapshot = {
            "weather": {"periods": periods},
            "alerts": alerts,
            "traffic": shared.get("traffic", []) if area.get("traffic") == "511nj" else [],
            "news": [],
        }
        facts = build_facts(snapshot, area={**area, "counties": None})
        text = rules_brief(facts)
        results[area["id"]] = {"label": area["label"], "topic": area["topic"], "text": text, "flags": impact_flags(facts)}
        print(f"[ok] {area['label']}: {text}")

        if args.send:
            try:
                send_ntfy(text, area["topic"], title=f"Local Pulse: {area['label']}")
                sent += 1
            except Exception as exc:
                failed += 1
                print(f"   send failed: {exc}")
            time.sleep(SEND_PAUSE_SECONDS)
        else:
            time.sleep(NWS_PAUSE_SECONDS)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "areaCount": len(areas), "sent": sent, "failed": failed, "briefs": results,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Areas: {len(areas)}, sent: {sent}, failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
