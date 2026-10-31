#!/usr/bin/env python3
"""Turn the collected local-conditions snapshot into one short, plain-language brief.

The brief is what Local Pulse sends to people's phones. It is written by Claude when an
ANTHROPIC_API_KEY is available, and by simple built-in rules when it is not, so the
pipeline never stops because the AI is unavailable.

Usage:
    python brief.py                       # write data/brief.json
    python brief.py --send                # also post it to the Telegram channel
    python brief.py --force               # rewrite even if nothing changed

Environment variables (all optional):
    ANTHROPIC_API_KEY        Lets Claude write the brief.
    LOCAL_PULSE_MODEL        Claude model to use (default: claude-haiku-5-5).
    TELEGRAM_BOT_TOKEN       Bot that posts the brief.
    TELEGRAM_CHAT_ID         Channel to post to, e.g. @localpulse_cnj.
    TELEGRAM_CHANNEL_URL     Public join link shown on the website, e.g. https://t.me/localpulse_cnj.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Area settings. Change these to point Local Pulse at a different area.
# ---------------------------------------------------------------------------
AREA_LABEL = "Central New Jersey"
LATITUDE = 40.2171
LONGITUDE = -74.7429
ROAD_RADIUS_MILES = 25
# NWS alerts are collected statewide; keep only the ones that name these counties.
COUNTIES = ("Mercer", "Middlesex", "Burlington", "Somerset", "Hunterdon", "Monmouth", "Bucks")
MAX_ROAD_EVENTS = 6
MAX_HEADLINES = 4
MAX_BRIEF_CHARS = 600

DEFAULT_MODEL = "claude-haiku-5-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = f"""You are Local Pulse, a local assistant that sends one short morning message to people in {AREA_LABEL}.
Your readers are everyday people: commuters, parents, people running errands. Many will only read the first line.

Write the message using ONLY the facts you are given. Rules:
- Lead with the single most important thing for getting around today.
- Plain everyday words. No jargon, no markdown, no bullet symbols, no hashtags, no emoji.
- At most 4 short sentences and under 450 characters.
- Name roads and towns exactly as given. Never invent a crash, closure, time or number.
- Mention weather only if it changes what people should do (rain gear, ice, heat, a warning).
- Mention a headline only if it clearly affects travel or plans today.
- If nothing notable is happening, say so in one friendly sentence and give the weather.
- Start with "Good morning, {AREA_LABEL}." """


# ---------------------------------------------------------------------------
# Picking the facts that matter
# ---------------------------------------------------------------------------
def miles_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) * 0.621371


def road_label(event: dict[str, Any]) -> str:
    text = f"{event.get('title', '')} {event.get('description', '')}".lower()
    if re.search(r"crash|accident|overturned|disabled vehicle", text):
        return "crash or incident"
    if event.get("type") == "construction":
        return "construction"
    if re.search(r"closed|closure|blocked", text):
        return "closure"
    return "road event"


def tidy_place(title: str) -> str:
    """'Betsy Ross Bridge westbound : Construction' -> 'Betsy Ross Bridge westbound'."""
    return re.sub(r"\s*:\s*(construction|incident|accident|crash|congestion)\s*$", "", title or "", flags=re.I).strip()


def nearby_roads(snapshot: dict[str, Any], lat: float = LATITUDE, lon: float = LONGITUDE,
                 radius: float = ROAD_RADIUS_MILES) -> list[dict[str, Any]]:
    seen: set[str] = set()
    found = []
    for event in snapshot.get("traffic", []):
        if event.get("latitude") is None or event.get("longitude") is None:
            continue
        distance = miles_between(lat, lon, event["latitude"], event["longitude"])
        if distance > radius:
            continue
        key = f"{event.get('type')}|{event.get('title')}|{event.get('description')}"
        if key in seen:
            continue
        seen.add(key)
        found.append({**event, "distanceMiles": round(distance, 1), "label": road_label(event)})
    # Incidents and closures matter more than routine construction; then nearest first.
    rank = {"crash or incident": 0, "closure": 1, "road event": 2, "construction": 3}
    found.sort(key=lambda e: (rank.get(e["label"], 4), e["distanceMiles"]))
    return found


def local_alerts(snapshot: dict[str, Any], counties: tuple[str, ...] = COUNTIES) -> list[dict[str, Any]]:
    pattern = re.compile("|".join(re.escape(c) for c in counties), re.IGNORECASE)
    return [a for a in snapshot.get("alerts", []) if pattern.search(a.get("area") or "")]


def weather_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    periods = (snapshot.get("weather") or {}).get("periods") or []
    if not periods:
        return {}
    temps = [p["temperature"] for p in periods if p.get("temperature") is not None]
    wettest = max(periods, key=lambda p: p.get("probabilityOfPrecipitation") or 0)
    now = periods[0]
    return {
        "now": f"{now.get('temperature')}°{now.get('temperatureUnit', 'F')}, {now.get('shortForecast', '')}".strip(", "),
        "low": min(temps) if temps else None,
        "high": max(temps) if temps else None,
        "maxRainChance": wettest.get("probabilityOfPrecipitation") or 0,
        "wettestHour": hour_label(wettest.get("startTime")),
        "hoursCovered": len(periods),
    }


def hour_label(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%-I %p")
    except ValueError:
        return ""


def build_facts(snapshot: dict[str, Any], today: datetime | None = None) -> dict[str, Any]:
    today = today or datetime.now()
    roads = nearby_roads(snapshot)
    return {
        "area": AREA_LABEL,
        "date": today.strftime("%A, %B %-d"),
        "special": "Halloween" if (today.month, today.day) == (10, 31) else "",
        "weather": weather_summary(snapshot),
        "weatherAlerts": [
            {"event": a.get("event"), "headline": a.get("title"), "severity": a.get("severity"),
             "instruction": (a.get("instruction") or "")[:300]}
            for a in local_alerts(snapshot)
        ],
        "roads": [
            {"what": e["label"], "where": tidy_place(e.get("title", "")), "detail": (e.get("description") or "")[:200],
             "milesAway": e["distanceMiles"]}
            for e in roads[:MAX_ROAD_EVENTS]
        ],
        "roadCounts": {
            "incidents": sum(1 for e in roads if e["label"] in ("crash or incident", "closure")),
            "construction": sum(1 for e in roads if e["label"] == "construction"),
        },
        "headlines": [n.get("title") for n in (snapshot.get("news") or [])[:MAX_HEADLINES] if n.get("title")],
    }


def facts_fingerprint(facts: dict[str, Any]) -> str:
    """Stable hash so the AI is only called again when something actually changed."""
    stable = {k: v for k, v in facts.items() if k != "headlines"}
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Writing the brief
# ---------------------------------------------------------------------------
def rules_brief(facts: dict[str, Any]) -> str:
    """Plain-language brief built without AI. Used when Claude is unavailable."""
    parts = [f"Good morning, {facts['area']}."]
    alerts = facts["weatherAlerts"]
    roads = facts["roads"]
    weather = facts["weather"]

    if alerts:
        first = alerts[0]
        parts.append(f"The weather service has a {first['event']} for parts of the area, so check it before you head out.")

    serious = [r for r in roads if r["what"] in ("crash or incident", "closure")]
    if serious:
        r = serious[0]
        more = f" and {len(serious) - 1} more nearby" if len(serious) > 1 else ""
        parts.append(f"Watch for a {r['what']} at {r['where']} ({r['milesAway']} mi away){more}.")
    elif facts["roadCounts"]["construction"]:
        n = facts["roadCounts"]["construction"]
        parts.append(f"No crashes nearby right now, but {n} construction zone{'s' if n != 1 else ''} could slow you down.")
    else:
        parts.append("Roads nearby look clear right now.")

    if weather:
        rain = weather.get("maxRainChance") or 0
        line = f"It's {weather['now']}"
        if weather.get("high") is not None:
            line += f", up to {weather['high']}°"
        line += "."
        if rain >= 50:
            line += f" Rain is likely around {weather['wettestHour']}, so bring an umbrella."
        elif weather.get("low") is not None and weather["low"] <= 36:
            line += " Watch for frost or slick spots early."
        parts.append(line)

    if facts.get("special") == "Halloween":
        parts.append("Trick-or-treating tonight? Bring a flashlight and watch for kids crossing.")

    text = " ".join(parts)
    return text[:MAX_BRIEF_CHARS]


def ai_brief(facts: dict[str, Any], api_key: str, model: str) -> str:
    body = {
        "model": model,
        "max_tokens": 300,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": "Today's facts as JSON:\n" + json.dumps(facts, indent=1, ensure_ascii=False)
                       + "\n\nWrite today's Local Pulse message.",
        }],
    }
    request = Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode(),
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read())
    text = "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise ValueError("Claude returned an empty brief")
    return text[:MAX_BRIEF_CHARS]


def impact_flags(facts: dict[str, Any]) -> list[str]:
    """Tag what the brief warned people about, for the 90-day log."""
    flags = []
    weather = facts.get("weather") or {}
    if facts["weatherAlerts"]:
        flags.append("weather alert")
    if any("flood" in (a.get("event") or "").lower() for a in facts["weatherAlerts"]):
        flags.append("flooding")
    if facts["roadCounts"]["incidents"]:
        flags.append("crash or closure")
    if facts["roadCounts"]["construction"]:
        flags.append("construction")
    if (weather.get("maxRainChance") or 0) >= 50:
        flags.append("rain")
    if weather.get("low") is not None and weather["low"] <= 36:
        flags.append("cold or frost")
    return flags or ["quiet day"]


def write_journal(brief: dict[str, Any], journal_dir: Path, day: str) -> Path:
    journal_dir.mkdir(parents=True, exist_ok=True)
    facts = brief["facts"]
    entry = {
        "date": day,
        "sentAt": brief["generatedAt"],
        "message": brief["text"],
        "writtenBy": "Claude (AI)" if brief["source"] == "ai" else "built-in rules",
        "flags": impact_flags(facts),
        "nearbyIncidents": facts["roadCounts"]["incidents"],
        "nearbyConstruction": facts["roadCounts"]["construction"],
        "weatherAlerts": [a["event"] for a in facts["weatherAlerts"]],
        "weather": facts.get("weather", {}),
        "screenshot": f"screens/{day}.jpg",
    }
    path = journal_dir / f"{day}.json"
    path.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def send_telegram(text: str, token: str, chat_id: str) -> None:
    data = urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram refused the message: {result}")


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=Path("data/local_conditions.json"))
    parser.add_argument("--output", type=Path, default=Path("data/brief.json"))
    parser.add_argument("--send", action="store_true", help="post the brief to the Telegram channel")
    parser.add_argument("--force", action="store_true", help="rewrite even if nothing changed")
    parser.add_argument("--journal", type=Path, help="also save today's brief to this 90-day log folder")
    args = parser.parse_args()

    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    facts = build_facts(snapshot)
    fingerprint = facts_fingerprint(facts)

    previous: dict[str, Any] = {}
    if args.output.exists():
        try:
            previous = json.loads(args.output.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}

    channel_url = os.environ.get("TELEGRAM_CHANNEL_URL", "").strip() or previous.get("channelUrl", "")
    unchanged = previous.get("fingerprint") == fingerprint and previous.get("text")

    if unchanged and not args.force:
        brief = previous
        print("Conditions unchanged; reusing the existing brief.")
    else:
        source, text, note = "rules", "", ""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if api_key:
            try:
                text = ai_brief(facts, api_key, os.environ.get("LOCAL_PULSE_MODEL", DEFAULT_MODEL))
                source = "ai"
            except Exception as exc:  # never let the AI stop the pipeline
                note = f"AI unavailable, used built-in summary: {exc}"
        if not text:
            text = rules_brief(facts)
        brief = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "area": AREA_LABEL,
            "text": text,
            "source": source,
            "fingerprint": fingerprint,
            "channelUrl": channel_url,
            "facts": facts,
        }
        if note:
            brief["note"] = note
        print(f"Wrote a new brief ({source}).")

    brief["channelUrl"] = channel_url
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    print(brief["text"])

    if args.journal:
        from zoneinfo import ZoneInfo
        day = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        print(f"Logged {write_journal(brief, args.journal, day)}")

    if args.send:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        if not (token and chat_id):
            print("Skipping send: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are not set.")
        else:
            send_telegram(brief["text"], token, chat_id)
            print(f"Sent to {chat_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
