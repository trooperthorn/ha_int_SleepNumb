#!/usr/bin/env python3
"""Preserve your full SleepIQ sleep history locally before the cloud drops it.

Sleep Number is severing cloud connectivity device-by-device; the nightly
sleep-health record (heart rate, respiration, HRV, SleepIQ score, restful/
restless, bed exits, per-session sleep number) is the most perishable data on
the account. This tool walks every month from your first recorded session to
today, saves the raw monthly JSON per sleeper, and writes a consolidated CSV of
per-session metrics.

    SIQ_EMAIL=you@example.com SIQ_PASS='...' \
        SIQ_ARCHIVE=/path/to/archive python tools/archive_history.py

Read-only. Idempotent: fully-archived past months are skipped on re-runs, so it
is safe to run nightly. Output is personal data and is written outside the repo.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
import http.cookiejar

API = "https://prod-api.sleepiq.sleepnumber.com/rest"
ECIM = "https://ecim.sleepnumber.com/v1/token"
CLIENT_ID = "2oa5825venq9kek1dnrhfp7rdh"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Accept-Version": "5.3.30", "Content-Type": "application/json", "Accept": "application/json",
}

_cj = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cj),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()),
)
_auth: dict[str, str] = {}


def _req(method: str, url: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in {**HEADERS, **_auth}.items():
        req.add_header(k, v)
    try:
        with _opener.open(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def login(email: str, password: str) -> None:
    st, txt = _req("POST", ECIM, {"Email": email, "Password": password, "ClientID": CLIENT_ID})
    if st not in (200, 201):
        raise SystemExit(f"login failed: {st} {txt[:200]}")
    _auth["Authorization"] = (json.loads(txt).get("data") or {}).get("AccessToken", "")
    _req("GET", f"{API}/user/jwt")


def months(start: dt.date, end: dt.date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield dt.date(y, m, 1)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main() -> int:
    try:
        email, password = os.environ["SIQ_EMAIL"], os.environ["SIQ_PASS"]
    except KeyError:
        print("Set SIQ_EMAIL and SIQ_PASS.", file=sys.stderr)
        return 2
    out = os.environ.get("SIQ_ARCHIVE", os.path.join(os.getcwd(), "sleepiq-archive"))
    os.makedirs(out, exist_ok=True)

    login(email, password)
    st, txt = _req("GET", f"{API}/sleeper")
    sleepers = json.loads(txt).get("sleepers", []) if st == 200 else []
    if not sleepers:
        print(f"no sleepers ({st})", file=sys.stderr)
        return 1

    today = dt.date.today()
    cur_month = (today.year, today.month)
    rows: list[dict] = []

    for s in sleepers:
        sid = s["sleeperId"]
        name = s.get("firstName") or sid
        first = s.get("firstSessionRecorded", "2020-01-01")[:10]
        start = dt.date.fromisoformat(first).replace(day=1)
        sdir = os.path.join(out, f"{name}_{sid}")
        os.makedirs(sdir, exist_ok=True)
        print(f"\n{name} ({sid})  from {start:%Y-%m}")

        got = 0
        for first_of in months(start, today):
            fpath = os.path.join(sdir, f"{first_of:%Y-%m}.json")
            is_current = (first_of.year, first_of.month) == cur_month
            if os.path.exists(fpath) and not is_current:
                data = json.load(open(fpath, encoding="utf-8"))
            else:
                st, txt = _req("GET", f"{API}/sleepData?interval=M1&sleeper={sid}&date={first_of:%Y-%m-%d}")
                if st != 200:
                    print(f"  {first_of:%Y-%m}: {st} (stop)")
                    break
                data = json.loads(txt)
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=1)
                time.sleep(0.15)
            days = data.get("sleepData", []) or []
            for day in days:
                for sess in day.get("sessions", []):
                    rows.append({
                        "sleeper": name, "date": day.get("date"),
                        "start": sess.get("startDate"), "end": sess.get("endDate"),
                        "sleep_score": sess.get("sleepQuotient"),
                        "heart_rate": sess.get("avgHeartRate"),
                        "resp_rate": sess.get("avgRespirationRate"),
                        "hrv": sess.get("hrv"),
                        "in_bed_s": sess.get("inBed"), "restful_s": sess.get("restful"),
                        "restless_s": sess.get("restless"), "out_of_bed": sess.get("outOfBed"),
                        "sleep_number": sess.get("sleepNumber"),
                        "total_snore_s": sess.get("totalSnoreTime"),
                        "is_final": sess.get("isFinalized"),
                    })
            if days:
                got += 1
        print(f"  archived {got} month(s) with data -> {sdir}")

    rows.sort(key=lambda r: (r["date"] or "", r["sleeper"]))
    csv_path = os.path.join(out, "sessions.csv")
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"\n{len(rows)} sessions -> {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
