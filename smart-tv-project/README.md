# LG webOS TV Dashboard

A lightweight, customizable home-screen dashboard for older LG webOS Smart TVs, built to run inside the TV's Developer Mode with no root, no firmware changes, and no system apps removed. Developed and tested against a 2018 UK-series set running webOS 4.4.3.

It turns a TV into an Apple-TV-inspired control screen: big app shortcuts you drive with the standard remote's D-pad, a clock and weather, music alarms, a night-time mode, a locally generated guest Wi-Fi QR code, and an ambient screensaver.

> Part of a set of miscellaneous home-automation experiments. Reversible by design: everything installs through Developer Mode and uninstalls cleanly.

## Features

- **D-pad navigation** tuned for the standard LG remote (no Magic Remote/pointer needed): directional focus that finds the nearest control by on-screen position.
- **App shortcuts** that launch installed apps by ID, with each app's real logo and brand color pulled from the TV at build time.
- **Clock** (12/24h) and **weather** from [Open-Meteo](https://open-meteo.com/) (no API key, no account), with city search that tolerates "City, ST" / "City" input.
- **Alarms** that fire while the app is open: repeat days, snooze/dismiss, a gradual-volume chime with a generated-tone fallback, or wake to music by opening a streaming app (YouTube, Pandora, Apple Music).
- **Night mode**: dim amber/gray clock on black, slow element drift, next-alarm readout, sleep timer, one-button bedtime, and an automatic schedule for overnight hours.
- **Guest Wi-Fi QR** generated entirely on the device (no online generator), with credentials kept in a git-ignored local file and pushed to the TV at runtime, never committed or packaged.
- **Ambient screensaver**: original slow-drifting gradient scenes with a clock overlay that cross-fade like aerial wallpapers, kept to CSS so it stays light on limited RAM.
- **Settings**: persistent, stored only in the app's local storage on the TV.

## Design constraints

This targets an old embedded Chromium (webOS 4.x) on a TV with ~860 MB of RAM, so:

- Plain HTML/CSS/JS, ES5, no frameworks or build step for the app itself.
- No CSS grid or flex-gap; layouts use flexbox and absolute positioning.
- A strict Content Security Policy limits network access to the weather endpoints only.
- Scenes and visuals are drawn in CSS/Canvas rather than shipped as video.

## Privacy

- No analytics, ads, accounts, or third-party scripts; nothing phones home.
- The CSP blocks any origin except the weather API.
- Secrets (Wi-Fi credentials, device keys) live in git-ignored local files and are never committed or included in the TV package. App logos copied from the TV are also git-ignored.

## Honest capability notes

Things that worked, and things the platform would not allow in Developer Mode, are documented so others don't chase dead ends:

- **Auto-start at power-on:** not possible without root. The activity-manager request to launch at power-on is refused ("doesn't have rights to call callback/trigger").
- **Live camera/WebRTC video:** not viable on this browser; still-image refresh is the realistic path.
- **Reading another app's "now playing":** not exposed to a Developer Mode app.
- **Forcing a streaming app to play:** blocked; the app can launch, but play has to be resumed by the app itself.

## Build and deploy

Requires [Node.js](https://nodejs.org/) and the [webOS CLI](https://www.npmjs.com/package/@webos-tools/cli), plus a TV with Developer Mode enabled and registered as a device named `lgtv`.

```
# optional: refresh app logos from the TV (keeps them out of git)
python scripts/fetch_logos.py

# package, install, and launch on the TV
powershell -File scripts/deploy.ps1
```

## Guest Wi-Fi setup

```
copy config.example.json config.local.json   # then fill in your network
python scripts/push_config.py                 # sends it straight to the TV
```

`config.local.json` is git-ignored and never leaves your machine except to the TV on your own network.

## Layout

```
app/            The dashboard (HTML/CSS/JS), packaged to the TV
  js/           store, nav, weather, alarms, night, screensaver, guest, ui
scripts/        Packaging, logo fetch, config push, asset generators
config.example.json   Template for local guest-Wi-Fi config
```

## License

[MIT](LICENSE)
