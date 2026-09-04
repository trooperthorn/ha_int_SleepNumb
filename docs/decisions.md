# Decisions

Dated decisions with the alternative rejected and why.

## 2026-09-04: The config flow keeps `async_update_reload_and_abort`

The `ha-dev-current` scanner flags the two reload sites in `config_flow.py`
because combining them with a config entry update listener becomes an error
in core 2026.12 (developer blog 2026-05-07). This integration registers no
update listener, so the flow's reloads are the only reload path and the rule
does not apply. Rejected: `async_update_and_abort`, which would leave a
changed host or credential unapplied until a manual reload.

## 2026-09-04: Comments inside the vendored `sleepiq_local` library stay

`custom_components/sleepnumber_pro/sleepiq_local/` is a localized copy of an
upstream library (`docs/FORK_PATCHES.md` lists the patches). Its comments are
left as upstream wrote them so the patch list stays the only diff; ruff and
mypy already exclude that directory for the same reason.

## 2026-09-04: HACS brands check ignored

The integration ships no brand assets and is not listed in
`home-assistant/brands`, so the HACS action runs with that check ignored.
Listing the brand upstream would let the ignore be removed. The license check
is skipped on feature branches only, because HACS reads license metadata from
the default branch.

## 2026-09-04: Minimum Home Assistant is 2026.9.0

The suite runs on `pytest-homeassistant-custom-component` 0.13.363, which pins
core 2026.9.0, so that is the only version the tests prove. Rejected: keeping
the 2026.7.0 floor, which no test exercised.

## 2026-09-04: Bridge validates `/raw` inputs and never uses a shell

CodeQL flagged `bridge/sleepnumber_bridge.py` for building a shell command
from request parameters (`py/command-line-injection`, critical). The bridge
now accepts only the documented pump keys (`KNOWN_KEYS`) and an `arg` of at
most 32 characters from `[A-Za-z0-9_.:-]`, rebuilds both from those
allow-lists so no request text reaches the process, splits the command
template into an argv list, and runs it with `shell=False`. A regex check
alone left CodeQL's taint analysis unsatisfied, and the allow-list is the
honest statement of what the bridge supports. The pump protocol only ever needs
four-letter keys and short alphanumeric arguments (`docs/LOCAL_ROOT.md`), so
the allow-list costs nothing. Rejected: keeping `shell=True` and quoting the
values, because quoting is the mechanism that has failed historically and the
hub's Python 2.7 has no `shlex.quote`. `tests/test_bridge.py` pins the
contract.

## 2026-09-04: `tools/inspect_bed.py` prints biometrics only on request

CodeQL flagged the sleep-health print (`py/clear-text-logging-sensitive-data`,
high). Heart rate, respiration, and HRV are the user's own data, printed to
their own console, but the tool is also run to capture logs for bug reports
and those logs travel. The tool now fetches and prints that record only with
`--biometrics`; the default output keeps presence, sleep number, and
pressure. Rejected: dismissing the alert, because the log-sharing case is
real.

