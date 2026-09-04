# On-hub bridge

`sleepnumber_bridge.py` runs **on the rooted SleepIQ hub** and exposes a tiny
local HTTP/JSON API so Home Assistant can read the bed without the cloud.

- Stdlib only, compatible with the hub's **Python 2.7.18**.
- Does not reimplement the pump wire protocol, it invokes the hub's existing
  vendor command tool (the 4-letter `PSNL`/`PSNS`/`LBPL` interface) and returns
  the result as JSON.

See [`../docs/LOCAL_ROOT.md`](../docs/LOCAL_ROOT.md) for the full root + install
procedure.

## Configure (environment variables)

| Var | Default | Meaning |
|-----|---------|---------|
| `SNB_CMD` | `/bam/scripts/bio {key} {arg}` | command template; `{key}`/`{arg}` filled per request |
| `SNB_PORT` | `8765` | listen port |
| `SNB_TOKEN` | *(none)* | optional shared secret; clients send `X-SNB-Token` |

## Endpoints

| Route | Returns |
|-------|---------|
| `GET /health` | `{"ok": true, "ts": ...}` |
| `GET /status` | merged snapshot: sleep number + presence per side |
| `GET /raw?key=PSNL&arg=` | raw stdout of one command, for calibration |

`key` must be exactly four upper-case letters and `arg` at most 32 characters
from `A-Z`, `a-z`, `0-9`, `_`, `.`, `:`, `-`; anything else returns 400 before
a process starts. The command template is split into an argv list and run
without a shell, so request values can never be interpreted as shell syntax.
Set `SNB_TOKEN`; without it any device on the LAN can drive the pump.

## Quick test

```sh
python sleepnumber_bridge.py &
curl http://localhost:8765/health
curl "http://localhost:8765/raw?key=PSNL"
```
