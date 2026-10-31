# Automated Local Conditions Monitor

This automation lab transforms public weather, road, and local news data into one practical answer: **what could affect your day before you leave?**

It collects current conditions, maps nearby disruptions, filters them by distance, and translates the results into plain language for commuting, errands, school, outdoor plans, and neighborhood events.

## Live Dashboard

[Open Before You Head Out](https://ronisha609.github.io/Automation/gsoc-intelligence-monitor/)

The dashboard shows:

- Current weather and rain probability for the selected area.
- Active National Weather Service alerts, including flooding.
- Nearby crashes, closures, and construction from NJDOT 511NJ.
- A GPS-centered map with adjustable 10, 25, and 50 mile views.
- Recent local headlines that could change travel or daily plans.
- A short, plain-language assessment of what the conditions mean.

Use **Use my location** for nearby results. The location remains in the browser and is used only to request public weather data and calculate distance from mapped road events.

## Automated Collection

GitHub Actions refreshes the shared data snapshot every 30 minutes. The collector preserves the status of each source, so a failed feed remains visible instead of silently disappearing.

| Source | What it contributes |
| --- | --- |
| National Weather Service | Hourly forecast, watches, warnings, advisories, and flood alerts |
| NJDOT 511NJ | Active crashes, closures, disabled vehicles, and construction |
| GDELT | Recent local reporting connected to traffic, weather, outages, schools, and events |

## Intelligence and Automation Skills

- Engineers a scheduled multi-source collection pipeline.
- Normalizes JSON, GeoJSON, and RSS into a usable data model.
- Applies GEOINT distance filtering and renders operational map layers.
- Separates official alerts, transport data, and media reporting by source.
- Converts raw feeds into clear decisions for a nontechnical audience.
- Preserves source failures and partial collection for honest reporting.
- Delivers a responsive public dashboard through GitHub Pages.

## Run Locally

The dashboard is a static page. Start a local server from the repository root:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/gsoc-intelligence-monitor/`.

Refresh its cached public data with:

```bash
cd gsoc-intelligence-monitor
python update_dashboard_data.py --output data/local_conditions.json
```

## Original Intelligence Monitor

The repository also includes the original Python alert monitor, which collects National Weather Service alerts, USGS earthquake data, and CISA Known Exploited Vulnerabilities, ranks the records, removes duplicates, and generates a concise intelligence brief.

```bash
cp config.example.json config.json
python monitor.py --config config.json --output output/brief.md
python -m unittest discover -s tests -v
```

## Source Documentation

- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)
- [NJDOT 511NJ](https://511nj.org/)
- [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [Leaflet](https://leafletjs.com/)
