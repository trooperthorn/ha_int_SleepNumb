#!/usr/bin/env python3
"""Inspect your Sleep Number bed directly through the vendored `sleepiq_local`
library — no Home Assistant required.

Reads credentials from the environment so nothing is written to disk:

    SIQ_EMAIL=you@example.com SIQ_PASS='...' python tools/inspect_bed.py

Prints the live picture (presence, sleep number, pressure) for every sleeper.
The latest sleep-health record (heart rate, respiration, HRV, SleepIQ score)
is biometric data and is fetched and printed only with --biometrics. This is
the same code path the integration's cloud transport uses.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Import the vendored fork from the component package.
PKG = Path(__file__).resolve().parents[1] / "custom_components" / "sleepnumber_pro"
sys.path.insert(0, str(PKG))

if sys.platform == "win32":
    # aiodns needs a selector loop on Windows; the integration runs under HA's
    # loop where this is handled — this shim only matters for the standalone tool.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiohttp  # noqa: E402
import sleepiq_local as siq  # noqa: E402


def _session() -> aiohttp.ClientSession:
    # Threaded resolver avoids environment-specific aiodns/pycares mismatches.
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver()))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--biometrics", action="store_true", help="also fetch and print last night's heart rate, respiration, HRV, and score")
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    try:
        email = os.environ["SIQ_EMAIL"]
        password = os.environ["SIQ_PASS"]
    except KeyError:
        print("Set SIQ_EMAIL and SIQ_PASS in the environment.", file=sys.stderr)
        return 2

    async with _session() as session:
        api = siq.AsyncSleepIQ(client_session=session)  # Cognito cookie auth by default
        await api.login(email, password)
        await api.init_beds()
        await api.fetch_bed_statuses()

        for bed in api.beds.values():
            foundation = bed.foundation.type or "(none / not connected)"
            print(f"\nBed: {bed.name!r}  model={bed.model}  foundation={foundation}")
            await bed.fetch_pause_mode()
            print(f"  privacy pause: {'on' if bed.paused else 'off'}")

            for sleeper in bed.sleepers:
                print(f"  - {sleeper.name} ({sleeper.side_full})")
                print(f"       in bed:       {sleeper.in_bed}")
                print(f"       sleep number: {sleeper.sleep_number}")
                print(f"       pressure:     {sleeper.pressure}")
                if not args.biometrics:
                    print("       last night:   not fetched (pass --biometrics to show)")
                    continue
                try:
                    await sleeper.fetch_sleep_data()
                    sd = getattr(sleeper, "sleep_data", None)
                    if sd:
                        hrs = round((sd.duration or 0) / 3600, 1)
                        print(f"       last night:   score={sd.sleep_score}  "
                              f"HR={sd.heart_rate}bpm  resp={sd.respiratory_rate}  "
                              f"HRV={sd.hrv}  duration={hrs}h")
                except Exception as err:  # noqa: BLE001 - report and continue
                    print(f"       sleep data:   unavailable ({err})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
