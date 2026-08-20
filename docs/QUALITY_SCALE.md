# Quality scale progress

Target: **exceed Platinum**. Home Assistant's quality scale is Bronze → Silver →
Gold → Platinum; this integration also pursues local-first operation, which the
scale does not itself require but which is the whole point here.

| Rule | Tier | Status |
|------|------|--------|
| Config flow, no YAML config | Bronze | ✅ |
| Unique IDs on all entities | Bronze | ✅ (`{sleeper_id}_{key}`) |
| `has_entity_name` throughout | Bronze | ✅ |
| Runtime data typed on the entry | Bronze | ✅ (`SleepNumberData`) |
| Test coverage of setup + config flow | Bronze | ✅ (10 tests) |
| Reauth flow | Silver | ✅ (Cognito re-login) |
| Graceful degradation of unavailable devices | Silver | ✅ (severed foundation never fails setup) |
| Coordinator-based polling | Silver | ✅ (3 coordinators) |
| Parallel updates safe | Silver | ✅ |
| Entities disabled by default where noisy | Gold | ✅ (raw pressure) |
| Diagnostics with redaction | Gold | ✅ (`diagnostics.py`) |
| Discovery | Gold | ✅ (DHCP, MAC `64:DB:A0:*`) |
| Devices + areas modelled | Gold | ✅ (hub device + per-sleeper devices) |
| Entity categories (config/diagnostic) | Gold | ✅ |
| Icon translations / translations | Gold | ✅ (`translations/en.json`) |
| Strict typing | Platinum | 🔶 partial — component typed; vendored lib not yet |
| Async dependency, no blocking I/O | Platinum | ✅ |
| Websocket/push or efficient polling | Platinum | 🔶 cloud polls; local push planned |
| **Local polling / no cloud reliance** | *beyond* | 🔶 architecture + bridge shipped; activates after hub root |

## What remains for Platinum

- Finish strict typing on the vendored `sleepiq_local` fork (upstream is loosely
  typed) and enable `mypy --strict` in CI for the component package.
- Local transport wired end-to-end once a bridge is installed, giving push-style
  latency and removing cloud reliance entirely.

## Beyond Platinum (the project's real goal)

Platinum still assumes a working cloud. This integration is built to outlive it:
the cloud transport is a fallback, the local hub bridge is the preferred path,
and your sleep history is archived locally so nothing is lost when Sleep Number's
servers go dark.
