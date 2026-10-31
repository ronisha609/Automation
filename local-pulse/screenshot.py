#!/usr/bin/env python3
"""Save a phone-sized screenshot of the live dashboard for the 90-day log.

Serves the repository locally, opens local-pulse/ in headless Chromium and saves a JPEG.
Run from the repository root:
    python local-pulse/screenshot.py --output local-pulse/journal/screens/2026-11-01.jpg
"""

from __future__ import annotations

import argparse
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                          timezone_id="America/New_York", locale="en-US")
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{args.port}/local-pulse/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2500)  # let the map tiles and live weather settle
            page.screenshot(path=str(args.output), type="jpeg", quality=70, full_page=False)
            browser.close()
    finally:
        server.shutdown()
    print(f"Saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
