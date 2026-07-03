# russrnet — Russound RNET (CAM6.6) for Home Assistant

A modern custom integration for the **Russound CAM6.6** multi-zone controller
over **RNET** (RS-232 via TCP serial bridge).

Replaces the legacy `russound_rnet` integration with:

- ✅ UI-based setup (config flow) — no YAML required
- ✅ Async, built on [`aiorussound`](https://github.com/noahhusby/aiorussound)
- ✅ One `media_player` entity per zone (power, volume, mute, source)
- ✅ Editable source names via options flow

## Requirements

- Home Assistant **2026.7.0** or newer
- Russound CAM6.6 connected via a TCP↔RS-232 bridge
  (e.g. USR-TCP232-302) configured at **19200 / 8 / N / 1**, TCP Server mode

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/sharespamnow/russrnet` (type: Integration)
3. Install **Russound RNET (CAM6.6)** and restart Home Assistant
4. Settings → Devices & Services → **Add Integration** → search "Russound RNET"

## Status

🚧 Work in progress — v0.1.0
