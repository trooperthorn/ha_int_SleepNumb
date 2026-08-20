"""Diagnostics for Sleep Number Local-First."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import SleepNumberConfigEntry

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    "macAddress",
    "mac_addr",
    "sleeperLeftId",
    "sleeperRightId",
    "email",
    "username",
    "zipcode",
    "zipCode",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SleepNumberConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = entry.runtime_data
    beds: dict[str, Any] = {}
    for bed_id, bed in data.client.beds.items():
        beds[bed_id] = {
            "name": bed.name,
            "model": bed.model,
            "paused": bed.paused,
            "foundation_type": bed.foundation.type or None,
            "responsive_air": bed.responsive_air,
            "sleepers": [
                {
                    "side": str(s.side),
                    "in_bed": s.in_bed,
                    "sleep_number": s.sleep_number,
                    "pressure": s.pressure,
                    "sleep_data": {
                        "sleep_score": s.sleep_data.sleep_score,
                        "heart_rate": s.sleep_data.heart_rate,
                        "respiratory_rate": s.sleep_data.respiratory_rate,
                        "hrv": s.sleep_data.hrv,
                        "duration": s.sleep_data.duration,
                    }
                    if s.sleep_data
                    else None,
                }
                for s in bed.sleepers
            ],
        }

    return {
        "capabilities": data.capabilities,
        "beds": async_redact_data(beds, TO_REDACT),
    }
