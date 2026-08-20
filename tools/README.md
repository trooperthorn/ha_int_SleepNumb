# tools

Standalone utilities that use the vendored `sleepiq_local` library directly — no
Home Assistant required. Credentials come from the environment; nothing is written
to disk.

```bash
SIQ_EMAIL='you@example.com' SIQ_PASS='your-password' python tools/inspect_bed.py
```

## `inspect_bed.py`

Logs in via Cognito and prints, for every sleeper:

- live presence, sleep number, and raw pressure
- last night's SleepIQ score, average heart rate, respiration, HRV, and duration

Useful for confirming the cloud path works for your account, and for capturing a
baseline of what data is still flowing before the cloud degrades further.
