#!/usr/bin/env python3
"""Roll the daily log entries into the 90-day summary shown on journal.html and in journal/README.md."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

FLAG_ORDER = ["crash or closure", "weather alert", "flooding", "rain", "cold or frost", "construction", "quiet day"]


def load_entries(journal_dir: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(journal_dir.glob("20*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entry["hasScreenshot"] = (journal_dir / entry.get("screenshot", "")).is_file()
        entries.append(entry)
    return entries


def summarize(entries: list[dict[str, Any]], start: str, days: int,
              requests: list[dict[str, Any]] | None = None, areas: dict[str, Any] | None = None) -> dict[str, Any]:
    counts = Counter(flag for e in entries for flag in e.get("flags", []))
    elapsed = (date.today() - date.fromisoformat(start)).days + 1 if start else len(entries)
    return {
        "start": start,
        "plannedDays": days,
        "dayNumber": max(0, min(days, elapsed)),
        "briefsSent": len(entries),
        "writtenByAI": sum(1 for e in entries if e.get("writtenBy", "").startswith("Claude")),
        "daysWith": {flag: counts.get(flag, 0) for flag in FLAG_ORDER},
        "screenshots": sum(1 for e in entries if e.get("hasScreenshot")),
        "townRequests": len(requests or []),
        "areasCovered": (areas or {}).get("areaCount", 0),
        "areaMessagesLastRun": (areas or {}).get("sent", 0),
    }


def write_readme(journal_dir: Path, summary: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    d = summary["daysWith"]
    lines = [
        "# Local Pulse: 90-Day Log",
        "",
        f"Started {summary['start']}. Day {summary['dayNumber']} of {summary['plannedDays']}. "
        f"Covering {summary['areasCovered']} areas, with {summary['townRequests']} town requests so far. "
        "Each morning GitHub Actions collects public data, writes one plain-language message, "
        "posts it, takes a screenshot and saves the entry here.",
        "",
        "| Briefs sent | Days with a crash or closure nearby | Weather alerts | Rain | Cold or frost | Quiet days |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| {summary['briefsSent']} | {d['crash or closure']} | {d['weather alert']} | {d['rain']} | {d['cold or frost']} | {d['quiet day']} |",
        "",
        "| Date | Message | Flagged | Screenshot |",
        "| --- | --- | --- | --- |",
    ]
    for e in reversed(entries):
        shot = f"[view]({e['screenshot']})" if e.get("hasScreenshot") else ""
        message = e.get("message", "").replace("|", "/")
        lines.append(f"| {e['date']} | {message} | {', '.join(e.get('flags', []))} | {shot} |")
    (journal_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, default=Path("journal"))
    parser.add_argument("--start", default="", help="first day of the 90-day run, YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--requests", type=Path, help="data/requests.json")
    parser.add_argument("--areas", type=Path, help="data/area_briefs.json")
    args = parser.parse_args()

    entries = load_entries(args.journal)
    start = args.start or (entries[0]["date"] if entries else date.today().isoformat())
    read = lambda p: json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else {}
    summary = summarize(entries, start, args.days, read(args.requests).get("requests", []), read(args.areas))
    index = {"summary": summary, "entries": list(reversed(entries))}
    args.journal.mkdir(parents=True, exist_ok=True)
    (args.journal / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    write_readme(args.journal, summary, entries)
    print(f"Journal: {summary['briefsSent']} entries, day {summary['dayNumber']} of {summary['plannedDays']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
