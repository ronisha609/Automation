#!/usr/bin/env python3
"""Save "Request my town" submissions to data/requests.json.

The website posts each request to a private ntfy topic, which also alerts the owner's phone.
ntfy.sh keeps messages for about 12 hours, so this runs with the 30-minute refresh and keeps a
permanent record (town and state only; no personal information is collected).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

REQUESTS_TOPIC = "local-pulse-requests-55f784"


def fetch_recent(topic: str) -> list[dict]:
    request = Request(f"https://ntfy.sh/{topic}/json?poll=1&since=12h", headers={"User-Agent": "Local-Pulse/1.0"})
    with urlopen(request, timeout=30) as response:
        lines = response.read().decode("utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]
    return [e for e in events if e.get("event") == "message"]


def merge(existing: list[dict], incoming: list[dict]) -> list[dict]:
    seen = {r["id"] for r in existing}
    for e in incoming:
        if e["id"] in seen:
            continue
        town = (e.get("message") or "").strip()[:120]
        if town:
            existing.append({"id": e["id"], "time": e.get("time"), "town": town})
            seen.add(e["id"])
    return sorted(existing, key=lambda r: r.get("time") or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/requests.json"))
    args = parser.parse_args()
    existing = json.loads(args.output.read_text(encoding="utf-8")).get("requests", []) if args.output.exists() else []
    merged = merge(existing, fetch_recent(REQUESTS_TOPIC))
    args.output.write_text(json.dumps({"requests": merged}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(merged)} town requests on record.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
