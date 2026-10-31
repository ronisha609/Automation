# Local Pulse

Local Pulse **converts live public data into one decision-ready message**. It fuses weather, flooding, crash, construction and local news feeds; isolates what affects people within 25 miles; and delivers a plain-language morning message to any phone at no cost.

[Live dashboard](https://ronisha609.github.io/Automation/local-pulse/) · [90-day field log](https://ronisha609.github.io/Automation/local-pulse/journal.html) · [Intelligence](https://github.com/ronisha609/Intelligence) · [Cybersecurity](https://github.com/ronisha609/CyberSecurity)

> Good morning, Central New Jersey. The weather service has a Frost Advisory for parts of the area, so check it before you head out. No crashes nearby right now, but 7 construction zones could slow you down. It's 41°F, Sunny, up to 60°.

*Generated from live NWS and 511NJ data, October 31, 2026.*

## Operational Pipeline

| Stage | Execution | Output |
| --- | --- | --- |
| Collect | Pulls NWS forecasts and alerts, 511NJ incidents and construction, and GDELT local reporting every 30 minutes | Unified snapshot with per-source status |
| Normalize | Parses JSON, GeoJSON and RSS into one data model; strips markup and duplicate records | Clean, comparable event records |
| Filter | Applies geodesic distance limits and county-level alert matching | Only events that touch the coverage area |
| Prioritize | Ranks crashes and closures above routine roadwork; flags rain, frost and flooding thresholds | An ordered set of facts that matter today |
| Synthesize | Constrains Claude to verified facts, plain language and 450 characters; falls back to deterministic rules | One message a nontechnical reader can act on |
| Disseminate | Pushes the message to subscribers' phones through ntfy and publishes it to the dashboard | Free delivery to anyone, no account required |
| Validate | Logs every message, captures a daily screenshot and tags what each message warned about | Public, auditable record of performance |

## Live Product

- **Morning message** pushed to any phone at 7:15 AM through the free ntfy app.
- **Dashboard** with a GPS-centered map, adjustable 10, 25 and 50 mile views, active alerts, road events and local headlines.
- **90-day field log** with every message, daily screenshots and running totals of crash, alert, rain and frost warnings.
- **Zero operating cost**: GitHub Actions, GitHub Pages, public data sources and ntfy delivery run free.

## Capabilities Demonstrated

- Engineers a scheduled multi-source collection pipeline that survives partial outages.
- Fuses official alerts, transportation data and open-source reporting while preserving source attribution.
- Applies GEOINT distance filtering and county-level geofencing to cut statewide noise down to local impact.
- Prioritizes events by operational impact, not by volume.
- Constrains AI output to verified facts, with a rule-based fallback that removes single points of failure.
- Disseminates decision-ready guidance to a public audience in under 450 characters.
- Validates real-world performance through a 90-day public log with timestamped evidence.
- Tests filtering, ranking, flagging and logging logic with automated unit tests.

## 90-Day Field Validation

From November 1, 2026, the morning workflow runs daily for 90 days, then stops automatically. Each run:

1. Collects fresh data and writes the morning message.
2. Pushes it to subscribers.
3. Captures a phone-sized screenshot of the live dashboard.
4. Tags the message: crash or closure, weather alert, flooding, rain, cold or frost, construction or quiet day.
5. Updates the [field log](https://ronisha609.github.io/Automation/local-pulse/journal.html) and [`journal/README.md`](journal/README.md).

## Subscribe

1. Install the free **ntfy** app from the App Store or Google Play ([ntfy.sh](https://ntfy.sh)).
2. Tap **+** and subscribe to **local-pulse-nj**.

## Deploy Your Own

Stand up Local Pulse for any U.S. area in about 15 minutes.

1. **Fork** this repository on GitHub.
2. **Set the coverage area.** In `brief.py`, change `AREA_LABEL`, `LATITUDE`, `LONGITUDE`, `ROAD_RADIUS_MILES` and `COUNTIES`. In `update_dashboard_data.py`, change `NWS_POINT` and the state in `NWS_ALERTS`.
3. **Swap the traffic feed** if you're outside New Jersey. Replace the two 511NJ URLs in `update_dashboard_data.py` with your state's 511 or DOT feed.
4. **Name your notification topic.** In `.github/workflows/local-pulse-morning.yml`, set `NTFY_TOPIC` to a unique name, such as `local-pulse-yourtown`.
5. **Set the test window.** In the same file, set `START_DATE` and `DAYS`.
6. **Publish the dashboard.** Go to **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`.
7. **Enable the workflows.** Open the **Actions** tab and turn on workflows for the fork.
8. **Run it once.** In **Actions**, open **Local Pulse morning message**, choose **Run workflow** and tick **Run even outside the 90-day window**.
9. **Subscribe** to your topic in the ntfy app and confirm the message arrives.

### Optional upgrades

| Setting | Location | Effect |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Settings → Secrets and variables → Actions → **Secrets** | Claude writes the message (one call per day; set a spending limit in the Claude Console) |
| `TELEGRAM_BOT_TOKEN` | Actions **Secrets** | Adds Telegram delivery (create the bot with @BotFather) |
| `TELEGRAM_CHAT_ID` | Actions **Variables** | Target channel, e.g. `@localpulse_yourtown` |
| `TELEGRAM_CHANNEL_URL` | Actions **Variables** | Shows a Telegram join button on the dashboard |

## Run Locally

```bash
cd local-pulse
python update_dashboard_data.py --output data/local_conditions.json
python brief.py --force
python -m unittest discover -s tests -v
cd .. && python -m http.server 8000
```

Open `http://localhost:8000/local-pulse/`.

## Repository Map

| File | Function |
| --- | --- |
| `update_dashboard_data.py` | Collects and normalizes every source into `data/local_conditions.json` |
| `brief.py` | Filters, ranks, writes and sends the morning message |
| `screenshot.py` | Captures the daily dashboard screenshot |
| `journal.py` | Builds the 90-day totals and log |
| `index.html` | Public dashboard |
| `journal.html` | Public 90-day field log |
| `monitor.py` | Original intelligence monitor: ranks NWS alerts, USGS earthquakes and CISA Known Exploited Vulnerabilities into a concise brief |

## Source Documentation

- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)
- [NJDOT 511NJ](https://511nj.org/)
- [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [ntfy](https://docs.ntfy.sh/)
- [Claude API](https://docs.claude.com)
- [Leaflet](https://leafletjs.com/)
