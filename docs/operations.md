# Operations

Configuration keys, credentials, and the standalone `tools/` scripts that sit
outside the Home Assistant integration itself.

## Nightly history archive (`tools/archive_nightly.ps1`, `tools/schedule_archive.ps1`)

`archive_nightly.ps1` wraps `tools/archive_history.py`. It reads SleepIQ
credentials from a local, git-ignored `.siq_env` file (`KEY=VALUE` lines) next
to the repo root, so no password is ever stored in the scheduled task or in
the repo:

```
SIQ_EMAIL=you@example.com
SIQ_PASS=your-password
# optional: SIQ_ARCHIVE=D:\somewhere\sleepiq-archive
# optional: SIQ_PYTHON=C:\path\to\python.exe
```

If `.siq_env` is missing, or `SIQ_EMAIL`/`SIQ_PASS` are unset, the wrapper
logs a message and exits cleanly rather than failing the scheduled task.

`schedule_archive.ps1` registers (or updates) a Windows Scheduled Task that
runs the wrapper nightly at 03:30 by default, in the current user's context
so no Windows password is stored:

```powershell
powershell -ExecutionPolicy Bypass -File tools\schedule_archive.ps1
```

Remove it with:

```powershell
Unregister-ScheduledTask -TaskName "SleepNumber History Archive" -Confirm:$false
```
