# Sleep Number (SleepIQ) — Local-First for Home Assistant

## SEE TOOLS ON HOW TO OBTAIN DATA, and How SleepNumber is able to determine the number of times you have Bedroom Activies.

A rework of the Home Assistant Sleep Number / SleepIQ integration, engineered to **survive the SleepIQ cloud** and to exceed the Home Assistant **Platinum** quality scale.

> **Why this exists:** Sleep Number filed for bankruptcy and the SleepIQ cloud is
> already degrading (the base/foundation subsystem returns `404 "No Foundation
> Device"`, and accounts are being force-migrated to Cognito auth that breaks the
> stock integration). This project treats the cloud as a *fallback*, and the hub
> on your own LAN as the *preferred* source of truth.

📋 **[Audit, protocol map & architecture](https://claude.ai/code/artifact/e9014191-8db3-4c27-80c8-13bbae897622)** — the full write-up this repo implements.

See [`docs/README.md`](docs/README.md) for the full documentation index.

---

## Architecture: local-first, cloud-fallback

The integration always prefers the transport closest to the hardware that is
currently answering, and falls back automatically:

| Priority | Transport | Status |
|----------|-----------|--------|
| 1 | **Bluetooth LE (MCR)** — the hub's own BLE radio; local, **no hardware modification**, in-range only | shipped: reads/sets sleep number and drives base presets — **recovers base control the cloud severed** ([`docs/BLUETOOTH.md`](docs/BLUETOOTH.md)) |
| 2 | **On-hub bridge** — a LAN daemon over the pump protocol; local, whole-home | shipped; needs a one-time UART root ([`docs/LOCAL_ROOT.md`](docs/LOCAL_ROOT.md)) |
| 3 | **Cloud (Cognito)** — hardened REST, JWT auth, full sleep-health archive | live now; automatic fallback |

The status coordinator tries the local bridge first and falls back to the cloud
each cycle, exposing which path is active as a **Connection** sensor. The same
intent (`set_sleep_number`, `read presence`, …) maps to a local command when a
local transport answers and a cloud call when it doesn't — degrading feature by
feature, never all-or-nothing.

## Status

| Phase | State |
|-------|-------|
| 0 · Recon + audit | ✅ complete — see the audit artifact above |
| 1 · Hardened cloud path | ✅ shipped — full component, 10 passing tests |
| 2 · Local UART transport | ✅ bridge + root guide shipped; activates after you root the hub |
| 3 · Exceed Platinum | ✅ blueprints, CI, diagnostics, quality-scale tracking |

### What's in the box

- **`custom_components/sleepnumber_pro/`** — the integration: Cognito config flow
  with reauth, **reconfigure**, DHCP + **Bluetooth LE discovery**, three
  coordinators with **local-first / cloud-fallback**, a hub device and per-sleeper
  devices, diagnostics, and entities for presence, sleep number, pressure, sleep
  score, heart rate, respiration, HRV, restful/restless durations, Responsive Air,
  privacy pause, calibrate, stop-pump, and a **Connection** sensor (local vs cloud).
- **`custom_components/sleepnumber_pro/sleepiq_local/`** — the forked library
  (Cognito default, graceful 404, Responsive Air), verified live end-to-end.
- **`bridge/`** + **[`docs/LOCAL_ROOT.md`](docs/LOCAL_ROOT.md)** — the on-hub bridge
  daemon and the UART root procedure (whole-home local path).
- **Bluetooth (MCR)** — [`docs/BLUETOOTH.md`](docs/BLUETOOTH.md), `mcr.py`,
  `bluetooth.py`, `tools/ble_scan.py`: the no-root local path over the hub's own
  BLE radio — reads/sets sleep number and drives base presets, recovering base
  control the cloud gave up.
- **`blueprints/`** — five cross-integration automations (weather, solar, severe
  weather, climate, goodnight). See [`docs/AUTOMATIONS.md`](docs/AUTOMATIONS.md).
- **`tools/`** — `inspect_bed.py` (see your live bed) and `archive_history.py` with
  a nightly scheduler to preserve your sleep history before the cloud drops it.

### Entities (per sleeper unless noted)

| Platform | Entities |
|----------|----------|
| `binary_sensor` | In bed (occupancy) |
| `sensor` | Sleep number, pressure*, sleep score, heart rate, respiratory rate, HRV, sleep duration, restful*, restless*, Connection (local/cloud, bed)* |
| `number` | Sleep number (firmness) |
| `select` | Base preset — Flat / Zero G / Read / Watch TV / Snore / Favorite (BLE; recovers severed base control) |
| `switch` | Responsive Air; privacy pause (bed) |
| `button` | Calibrate (bed); stop pump (bed) |

<sub>* disabled by default / diagnostic.</sub>

## The forked library

`sleepiq_local` is a fork of [`asyncsleepiq`](https://github.com/kbickar/asyncsleepiq),
vendored directly into the component (no PyPI dependency) so it can carry local-transport
changes ahead of upstream. The two shipped fixes:

1. **Cognito cookie auth by default.** Stock `asyncsleepiq` defaults to the legacy `_k`
   key method, which now returns `401 "Session is invalid"` on every per-bed endpoint
   for migrated accounts. This fork defaults to the ecim-token → JWT cookie method.
2. **Graceful `404`.** A `404` (e.g. a disconnected foundation) no longer triggers a
   login-retry loop and no longer fails the whole coordinator update.

## Installation

**HACS (custom repository):** add `https://github.com/trooperthorn/ha_int_SleepNumb`
as an Integration repository, install "Sleep Number (SleepIQ) Local-First", restart
Home Assistant, then **Settings → Devices & Services → Add Integration → Sleep
Number**. Sign in with your SleepIQ email and password.

**Manual:** copy `custom_components/sleepnumber_pro/` into your HA `config/custom_components/`
directory and restart.

The integration works over the cloud immediately. To go fully local and recover
base control that Sleep Number has cut, follow [`docs/LOCAL_ROOT.md`](docs/LOCAL_ROOT.md).

## Preserve your history

```bash
SIQ_EMAIL='you@example.com' SIQ_PASS='your-password' python tools/archive_history.py
```

Saves every night's sleep-health record (heart rate, respiration, HRV, score) to
local JSON + CSV. Schedule it nightly with `tools/schedule_archive.ps1` (Windows).

## Development

```bash
pip install homeassistant pytest-homeassistant-custom-component
pytest -q
```

`tools/` scripts read credentials from `SIQ_EMAIL` / `SIQ_PASS` env vars.

## Credits

Cloud protocol derived from [`asyncsleepiq`](https://github.com/kbickar/asyncsleepiq)
by Keilin Bickar. Local hub root technique documented by
[Dillan Mills](https://dillan.org/articles/how-to-get-root-access-to-your-sleep-number-bed).
