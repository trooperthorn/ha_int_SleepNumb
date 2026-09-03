# Security Policy

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, private
addresses, or logs. Use GitHub's private vulnerability-reporting feature for
this repository. If private reporting is unavailable, open a minimal issue
asking the maintainer to establish a private channel; omit technical details.

Include the affected version/commit, prerequisites, impact, a minimal
reproduction, and suggested remediation. Remove tokens, API keys, cookies,
usernames, and private network details.

## Response targets

These are project targets, not an SLA: acknowledge critical/high reports in
three business days, establish severity and containment in seven, and publish
a coordinated fix/advisory as soon as safely validated. Lower-severity issues
are prioritized by exploitability and impact.

## Supported version

Only the latest published release and the default branch receive security
fixes. Operators should update Home Assistant and this integration promptly
and retain a tested rollback/backup.

## Security boundaries

Sleep Number (SleepIQ) Local-First is a privileged Home Assistant
integration, not a sandbox. It cannot prevent a malicious integration in the
same Python process from reading shared memory or files. It stores SleepIQ
cloud credentials (and an optional local-bridge shared secret) in the Home
Assistant config entry, which is only as protected as the Home Assistant
instance itself. The on-hub bridge daemon under `bridge/` runs with root
access on a rooted SleepIQ hub outside Home Assistant's process boundary; see
[`docs/LOCAL_ROOT.md`](docs/LOCAL_ROOT.md) for what that root access grants
and how it is used. The BLE transport sends unauthenticated MCR commands to
any bed hub in range that matches the configured address; this is the same
trust model the stock SleepIQ app uses over BLE.
