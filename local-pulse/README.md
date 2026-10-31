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
| Synthesize | Generates the brief with AI from verified facts only, with an automatic rule-based fallback | One message a nontechnical reader can act on |
| Disseminate | Pushes the message to subscribers' phones through ntfy and publishes it to the dashboard | Free delivery to anyone, no account required |
| Validate | Logs every message, captures a daily screenshot and tags what each message warned about | Public, auditable record of performance |

## Live Product

- **Morning message** pushed to any phone at 7:15 AM through the free ntfy app, covering all 21 New Jersey counties and 47 major U.S. cities.
- **Any U.S. town** on the dashboard: search by town or ZIP for live weather, alerts and news.
- **Request my town**: residents outside coverage request their area; requests alert the owner instantly and are logged as demand.
- **Dashboard** with a GPS-centered map, adjustable 10, 25 and 50 mile views, active alerts, road events and local headlines.
- **90-day field log** with every message, daily screenshots and running totals of crash, alert, rain and frost warnings.
- **Zero operating cost**: GitHub Actions, GitHub Pages, public data sources and ntfy delivery run free.

## Capabilities Demonstrated

- Engineers a scheduled multi-source collection pipeline that survives partial outages.
- Fuses official alerts, transportation data and open-source reporting while preserving source attribution.
- Applies GEOINT distance filtering and county-level geofencing to cut statewide noise down to local impact.
- Prioritizes events by operational impact, not by volume.
- Grounds AI output in verified facts, with a fallback that removes single points of failure.
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

1. Open the [dashboard](https://ronisha609.github.io/Automation/local-pulse/) and search your town.
2. Install the free **ntfy** app and subscribe to the topic it shows, such as **local-pulse-nj** or **local-pulse-va-richmond**.

## Build Your Own

Local Pulse is one configuration of a pattern anyone can adapt to their own community. The core choices:

| Decision | Options | Local Pulse |
| --- | --- | --- |
| Coverage | Any area served by public weather, traffic and news feeds | 21 NJ counties with live traffic, 47 major U.S. cities, and towns added on request |
| Brief writer | AI model, rule-based logic, or both | AI-assisted with a rule-based fallback, so delivery never depends on a paid service |
| Delivery | Push notification app, messaging channel, SMS, email or a web page | Free push notifications plus a public dashboard |
| Schedule | Fixed morning brief, change-triggered alerts, or both | Daily morning brief, data refreshed every 30 minutes |
| Validation | Private testing or a public performance record | 90-day public field log with daily screenshots |
| Cost | Free tiers through pay-per-use services | $0 on free tiers; AI is the only optional cost |

## Source Documentation

- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)
- [NJDOT 511NJ](https://511nj.org/)
- [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [ntfy](https://docs.ntfy.sh/)
- [Claude API](https://docs.claude.com)
- [Leaflet](https://leafletjs.com/)
