#!/usr/bin/env python3
"""Scan for the Sleep Number bed over Bluetooth LE and dump its GATT table.

BLE is a local path that needs no hub rooting -- just a Bluetooth adapter within
~8 feet of the bed. This tool finds the bed's smart hub, connects, and prints
every service / characteristic (with properties), so you can capture the exact
UUIDs and command channels for your specific model. The read/write/notify
characteristics under the Sleep Number service are how you read status and send
commands locally.

    pip install bleak
    python tools/ble_scan.py            # scan + list candidates
    python tools/ble_scan.py <ADDRESS>  # connect to one and dump its GATT

Reference: Sleep Number smart hubs advertise a custom service
09d23fae-90e6-44c2-95b6-0b3d0f1abf25 (observed on the Climate 360). Yours may
differ -- this tool reports whatever it finds.
"""
from __future__ import annotations

import asyncio
import sys

SN_SERVICE = "09d23fae-90e6-44c2-95b6-0b3d0f1abf25"

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("Install bleak first:  pip install bleak", file=sys.stderr)
    raise SystemExit(2)


def _looks_like_bed(name: str | None, uuids: list[str]) -> bool:
    name = (name or "").lower()
    if any(k in name for k in ("sleep", "sn ", "select comfort", "flexfit")):
        return True
    return SN_SERVICE.lower() in [u.lower() for u in uuids]


async def scan() -> None:
    print("Scanning 12s for BLE devices (get within ~8 ft of the bed)...")
    devices = await BleakScanner.discover(timeout=12.0, return_adv=True)
    hits = []
    for dev, adv in devices.values():
        uuids = list(adv.service_uuids or [])
        flag = "  <-- likely bed" if _looks_like_bed(adv.local_name or dev.name, uuids) else ""
        print(f"  {dev.address}  rssi={adv.rssi}  name={adv.local_name or dev.name!r}{flag}")
        if flag:
            hits.append(dev.address)
    if hits:
        print("\nLikely bed(s):", ", ".join(hits))
        print("Dump its GATT with:  python tools/ble_scan.py", hits[0])
    else:
        print("\nNo obvious bed found. Re-run closer to the bed, or pass an address to dump.")


async def dump(address: str) -> None:
    print(f"Connecting to {address} ...")
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}\n")
        for service in client.services:
            print(f"[service] {service.uuid}  ({service.description})")
            for ch in service.characteristics:
                props = ",".join(ch.properties)
                print(f"    [char] {ch.uuid}  ({props})  {ch.description}")
                if "read" in ch.properties:
                    try:
                        val = await client.read_gatt_char(ch.uuid)
                        print(f"           read -> {val.hex()}")
                    except Exception as err:  # noqa: BLE001
                        print(f"           read failed: {err}")


def main() -> int:
    if len(sys.argv) > 1:
        asyncio.run(dump(sys.argv[1]))
    else:
        asyncio.run(scan())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
