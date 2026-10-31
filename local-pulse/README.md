# Local Pulse

Local Pulse turns public weather, flooding, traffic and local news data into **one short morning message** that anyone can act on: a commuter, a parent, someone running errands. Nobody has to check five websites or learn a new app. They get one message that says what matters today.

> Good morning, Central New Jersey. The weather service has a Frost Advisory for parts of the area, so check it before you head out. No crashes nearby right now, but 7 construction zones could slow you down. It's 41°F, Sunny, up to 60°.

**[Open the live dashboard](https://ronisha609.github.io/Automation/local-pulse/)** · **[See the 90-day log](https://ronisha609.github.io/Automation/local-pulse/journal.html)**

## How it works

```
Every 30 minutes                    Every morning (90-day test)
─────────────────                   ─────────────────────────────
National Weather Service ─┐         snapshot ─► pick what matters ─► write the message ─► send to phones
NJDOT 511NJ crashes/work  ├─► snapshot          (distance, county,    (Claude AI, or       (Telegram channel)
GDELT local news         ─┘   (data/)            severity)             built-in rules)          │
                                                                                               ▼
                                                     screenshot the dashboard ─► save to the 90-day log
```

1. **Collect.** `update_dashboard_data.py` pulls weather, alerts, crashes, construction and headlines every 30 minutes and records which sources worked.
2. **Pick what matters.** `brief.py` keeps only road events within 25 miles, alerts for nearby counties and weather that changes plans, ranking crashes above routine roadwork.
3. **Write the message.** If an `ANTHROPIC_API_KEY` is set, Claude writes the message from those facts under strict rules (only the given facts, plain words, under 450 characters). Otherwise built-in rules write it, so the pipeline never depends on a paid service.
4. **Deliver.** The message is posted to a public Telegram channel anyone can join, and shown at the top of the dashboard.
5. **Keep the evidence.** Each morning's message, a phone-sized screenshot and tags for what it warned about are saved to `journal/` and shown on the 90-day log page.

## The 90-day test

From November 1, 2026, the morning workflow runs for 90 days and then stops by itself. The log tracks:

- every message sent and whether AI or rules wrote it
- days with a crash or closure nearby, weather alerts, flooding, rain and cold warnings
- a screenshot of the dashboard each day

## Cost

Everything runs free on a public GitHub repository: the data sources, GitHub Actions, GitHub Pages and Telegram. The AI is optional. With a key, it is called once a day, and a monthly spending limit can be set in the Claude Console.

## Setup

| What | Where | Needed? |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Settings → Secrets and variables → Actions → **Secrets** | Optional. Lets Claude write the message. |
| `TELEGRAM_BOT_TOKEN` | Actions **Secrets** | Optional. From @BotFather on Telegram. |
| `TELEGRAM_CHAT_ID` | Actions **Variables** | Optional. The channel, e.g. `@localpulse_cnj`. |
| `TELEGRAM_CHANNEL_URL` | Actions **Variables** | Optional. Join link shown on the site, e.g. `https://t.me/localpulse_cnj`. |

To change the area, edit the settings at the top of `brief.py` and the coordinates in `update_dashboard_data.py`.

## Run locally

```bash
cd local-pulse
python update_dashboard_data.py --output data/local_conditions.json
python brief.py --force                      # writes data/brief.json
python -m unittest discover -s tests -v
cd .. && python -m http.server 8000          # then open http://localhost:8000/local-pulse/
```

## Skills demonstrated

- **OSINT collection:** a scheduled multi-source pipeline over JSON, GeoJSON and RSS, with source failures kept visible.
- **Intelligence analysis:** filtering by distance, county and severity, then ranking what affects people most.
- **AI with guardrails:** the model gets only verified facts and strict rules, with a rule-based fallback.
- **Automation:** GitHub Actions for the 30-minute refresh, morning delivery, screenshots and logging.
- **Communication:** turning raw feeds into one plain sentence a nontechnical reader can act on.

## Also in this folder

`monitor.py` is the original intelligence monitor. It ranks National Weather Service alerts, USGS earthquakes and CISA Known Exploited Vulnerabilities into a short brief.

```bash
cp config.example.json config.json
python monitor.py --config config.json --output output/brief.md
```

## Sources

- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)
- [NJDOT 511NJ](https://511nj.org/)
- [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [Claude API](https://docs.claude.com)
- [Leaflet](https://leafletjs.com/)
