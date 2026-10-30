"""Copies each installed app's own logo from the TV into app/logos/ and writes logos.js.

The logos belong to their owners, so app/logos/ stays out of Git and is only packaged
for this TV. Run again after adding shortcuts. Needs the pairing in ~/.lgtv.
"""
import json
import os
import shutil
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".lgtv"))
import ssap  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
OUT = os.path.join(ROOT, "logos")

ws = ssap.connect(timeout=15)
points = ssap.call(ws, "ssap://com.webos.applicationManager/listLaunchPoints")["payload"]["launchPoints"]

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
logos = {}
for lp in points:
    url = lp.get("largeIcon") or lp.get("icon") or ""
    if not url.startswith("http://"):
        continue
    name = "".join(c if c.isalnum() else "_" for c in lp["id"]) + ".png"
    try:
        data = urllib.request.urlopen(url, timeout=8).read()
    except OSError as e:
        print("skipped", lp["id"], e)
        continue
    if data[:4] != b"\x89PNG":
        print("skipped", lp["id"], "not a PNG")
        continue
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(data)
    logos[lp["id"]] = {"file": "logos/" + name, "color": lp.get("iconColor") or ""}

with open(os.path.join(OUT, "logos.js"), "w") as f:
    f.write("var LOGOS = " + json.dumps(logos, indent=1) + ";\n")
total = sum(os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT))
print(f"{len(logos)} logos, {total / 1024:.0f} KB")
