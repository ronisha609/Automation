# Automated GSOC Intelligence Monitor

This automation lab collects official public alerts, filters them against a monitored location and time window, ranks each item, removes duplicates, and generates a concise GSOC-style intelligence brief.

The monitor combines **OSINT collection, API automation, GEOINT filtering, alert triage, source validation, intelligence writing, and decision support** in one repeatable workflow.

## Operational Workflow

1. Collect active weather alerts from the National Weather Service.
2. Filter USGS earthquake data by distance from the monitored location.
3. Identify recent additions to CISA's Known Exploited Vulnerabilities catalog.
4. Normalize records into one intelligence-item structure.
5. Assign transparent High, Moderate, or Low priorities.
6. Remove duplicate records and rank the remaining items.
7. Generate a Markdown brief with indicators, actions, official links, and collection status.

## Capabilities Demonstrated

- Engineers a multi-source collection workflow with Python and public APIs.
- Applies location filtering with the Haversine distance formula.
- Converts incompatible government data formats into one structured model.
- Prioritizes alerts through documented severity and urgency rules.
- Preserves collection failures instead of silently dropping unavailable sources.
- Produces a decision-ready brief while separating automation from analyst judgment.
- Protects residential privacy by using configurable coordinates instead of a street address.

## Official Data Sources

| Source | Intelligence value | Endpoint |
| --- | --- | --- |
| National Weather Service | Active watches, warnings, and advisories for a configured point | `https://api.weather.gov/alerts/active` |
| U.S. Geological Survey | Recent earthquake data in GeoJSON | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson` |
| CISA Known Exploited Vulnerabilities | Vulnerabilities confirmed as exploited in the wild | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` |

## Quick Start

Python 3.10 or newer is recommended. The project uses only the Python standard library.

```bash
cp config.example.json config.json
python monitor.py --config config.json --output output/brief.md
```

Use an approximate location or city center. A home address is unnecessary.

### Offline demonstration

```bash
python monitor.py --config config.example.json --demo \
  --output examples/sample_brief.md \
  --json-output examples/sample_items.json
```

Demo records are fictional and labeled. They validate parsing, scoring, deduplication, and report generation without presenting invented data as current intelligence.

## Configuration

| Field | Purpose |
| --- | --- |
| `location_label` | Human-readable location used in the brief |
| `latitude` / `longitude` | Approximate point for weather and distance filtering |
| `earthquake_radius_km` | Maximum distance for USGS events |
| `cisa_lookback_days` | Number of days to retain new CISA KEV entries |
| `max_items` | Maximum number of ranked items in the brief |
| `user_agent` | Contact identifier requested by public API operators |

The location can also be set without editing a file:

```bash
MONITOR_LOCATION="Central New Jersey" \
MONITOR_LAT="40.2171" \
MONITOR_LON="-74.7429" \
python monitor.py
```

## Priority Logic

- **NWS:** Severe or Extreme alerts and Immediate urgency are High priority.
- **USGS:** Tsunami flags, orange/red impact alerts, or magnitude 5.0+ events are High priority. Magnitude 3.5+ or events within 100 km are Moderate.
- **CISA KEV:** New entries associated with known ransomware campaigns are High priority; other recent entries are Moderate.

These rules support triage. They do not replace source verification, organizational exposure checks, local context, or analyst judgment.

## Validation

```bash
python -m unittest discover -s tests -v
```

The tests validate severity mapping, geographic filtering, CISA recency handling, deduplication, and risk ranking.

## Intelligence Value

The finished lab proves the ability to build the collection pipeline and evaluate its output. It demonstrates the same workflow used in GSOC and intelligence functions: define what matters, collect from reliable sources, filter noise, rank risk, identify collection failures, and deliver clear action.

## Source Documentation

- [NWS API Web Service](https://www.weather.gov/documentation/services-web-api)
- [NWS Alerts Web Service](https://www.weather.gov/documentation/services-web-alerts)
- [USGS Earthquake GeoJSON Feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
