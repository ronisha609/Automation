"""Sends the Guest Wi-Fi details from config.local.json straight to the app on the TV.

config.local.json is ignored by Git and is not in the TV package. The TV keeps the
details in the app's own storage. Nothing is printed except the network name.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".lgtv"))
import ssap  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PATH = os.path.join(ROOT, "config.local.json")

if not os.path.exists(PATH):
    sys.exit("No config.local.json. Copy config.example.json to that name and fill it in.")
with open(PATH, encoding="utf-8-sig") as f:
    guest = json.load(f)["guestWifi"]
if not guest.get("ssid") or guest["ssid"].startswith("YOUR"):
    sys.exit("Fill in the real network name in config.local.json first.")

ws = ssap.connect(timeout=15)
msg = ssap.call(ws, "ssap://system.launcher/launch", {"id": "com.local.lgdashboard", "params": {"guestWifi": guest}})
if msg.get("payload", {}).get("returnValue"):
    print("Sent to the TV for network:", guest["ssid"])
else:
    sys.exit("The TV did not accept it: " + str(msg.get("error")))
