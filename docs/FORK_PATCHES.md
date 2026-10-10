# `sleepiq_local` fork patches

`custom_components/sleepnumber_pro/sleepiq_local/` is a vendored fork of
[`asyncsleepiq`](https://github.com/kbickar/asyncsleepiq) (cloned from `master`,
2026-08-20). Vendored rather than pip-required so the local-transport work can land
ahead of upstream, and so the exact code is auditable in-tree.

Changes so far are minimal and surgical; everything else is upstream.
`asyncsleepiq` is distributed under the MIT License; this repository's own
[`LICENSE`](../LICENSE) covers the project as a whole.

## 1. Default to Cognito cookie auth (`api.py`, `asyncsleepiq.py`)

**Problem.** Upstream defaults `login_method=LOGIN_KEY`. On a Cognito-migrated
account the legacy `_k` key returns `401 {"Error":{"Code":50002,"Message":"Session
is invalid"}}` on every per-bed endpoint (`/bed/{id}/pauseMode`, `/foundation/*`,
`bamkey`, `/sleepData`). The library's retry loop just re-logs-in with the same key
and re-fails, so the integration lands in a permanent reauth prompt.

**Change.** Default `login_method` is now `LOGIN_COOKIE` in both `SleepIQAPI.__init__`
and `AsyncSleepIQ.__init__`. The cookie path posts to `ecim.sleepnumber.com/v1/token`,
sets the `Authorization` bearer, and completes the `/rest/user/jwt` handshake. The
`Accept-Version: 5.3.30` header (already upstream) keeps HRV populated.

**Verified.** `tools/inspect_bed.py` logs in and pulls presence, sleep number,
pressure, pause mode, and the full sleep-health record (HR / respiration / HRV /
score) live. The legacy key path remains available via `login_method=LOGIN_KEY`.

## 2. `404` is not an auth failure (`api.py`, `__make_request`)

**Problem.** The request layer retried login on both `401` **and** `404`, then
raised `SleepIQAPIException`. A `404` is not a session problem, it is a real
"not found," e.g. `/foundation/status → 404 "No Foundation Device"` when a base is
disconnected (the current state of the test bed). The retry-then-raise turned a
single missing subsystem into a whole-coordinator `UpdateFailed`, taking every
entity offline including the ones still reporting fine.

**Change.** Only `401` triggers the re-login retry. A `404` is raised as
`SleepIQAPIException(404, …)` for callers to handle. Foundation discovery already
probes with `check()` (a boolean `GET`), so an absent foundation now degrades to
"no foundation features" instead of failing the update.

**Verified.** `init_beds()` against the test bed reports foundation type `(none)`
and continues; bed status and sleep data still load.

## 3. Transport failures are not login failures (`api.py`, `exceptions.py`)

**Problem.** `login()` wrapped every non-timeout exception as
`SleepIQLoginException("Connection failure: ...")`. A DNS or socket failure during
the token call therefore looked like rejected credentials. The integration mapped
that to `ConfigEntryAuthFailed`, and Home Assistant opened a reauth flow against a
working account (seen live on 2026-10-09 during a DNS outage: `Cannot connect to
host ecim.sleepnumber.com:443 ... Timeout while contacting DNS servers`). The same
wrapping also re-labelled a genuine `SleepIQLoginException` raised inside
`login_key` / `login_cookie` as a "Connection failure".

**Change.** New `SleepIQConnectionException`. In `login()`, `aiohttp.ClientConnectionError`
and `OSError` (which cover `ClientConnectorError`, `ClientConnectorDNSError`,
`ClientOSError`, and `ServerDisconnectedError`) raise it; `SleepIQLoginException`
and `SleepIQTimeoutException` pass through unchanged; only the remaining
unexpected errors (for example a login payload without the expected key) stay a
login failure. `__make_request` raises the same exception for transport errors on
data calls, so the coordinators see one type instead of a raw aiohttp error.

**Integration side.** `coordinator._reraise` maps it to `UpdateFailed`, setup maps
it to `ConfigEntryNotReady`, and the config flow reports `cannot_connect`. The
settings coordinator also treats a timeout or transport error on the pause-mode
and Responsive Air calls as `UpdateFailed` instead of letting it escape as an
"Unexpected error". Covered by `tests/test_connection_errors.py`.

## Planned fork work (Phase 2)

- Transport interface: a `Transport` protocol with `CloudTransport` (this REST code)
  and `LocalHubTransport` (the on-hub bridge), selected by reachability.
- Local hub driver speaking the pump serial protocol via the on-hub bridge daemon.
- Typed models for the sleep-health payload and per-session archive.
