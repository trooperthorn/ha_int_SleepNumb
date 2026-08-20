"""Tests for the local-bridge response parser (pure logic, no network)."""

from __future__ import annotations

from custom_components.sleepnumber_pro.local import LocalStatus, parse_status


def test_parse_status_typical():
    snap = parse_status(
        {
            "sleep_number_left": "35",
            "sleep_number_right": "PSN=60",
            "in_bed_left": "out",
            "in_bed_right": "IN",
        }
    )
    assert snap == LocalStatus(
        sleep_number_left=35,
        sleep_number_right=60,
        in_bed_left=False,
        in_bed_right=True,
    )


def test_parse_status_missing_and_garbage():
    snap = parse_status({"sleep_number_left": None, "in_bed_right": "???"})
    assert snap.sleep_number_left is None
    assert snap.in_bed_right is None
