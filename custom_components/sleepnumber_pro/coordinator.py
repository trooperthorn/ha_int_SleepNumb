"""Data update coordinators for Sleep Number (SleepIQ) Local-First.

Design goal from the audit: never let one severed subsystem take the whole
integration down.  Sleep Number is decommissioning device connectivity feature
by feature, so every fetch degrades independently — a foundation that the cloud
now reports as absent must not blank out the live bed-sensor entities.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .sleepiq_local import (
    AsyncSleepIQ,
    SleepIQAPIException,
    SleepIQLoginException,
    SleepIQTimeoutException,
)
from .const import (
    DOMAIN,
    SETTINGS_INTERVAL,
    SLEEP_DATA_INTERVAL,
    STATUS_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type SleepNumberConfigEntry = ConfigEntry[SleepNumberData]


@dataclass
class SleepNumberData:
    """Runtime data stored on the config entry."""

    client: AsyncSleepIQ
    status: SleepNumberStatusCoordinator
    settings: SleepNumberSettingsCoordinator
    sleep: SleepNumberSleepDataCoordinator
    # Capability flags discovered at setup, surfaced to platforms.
    capabilities: dict[str, bool] = field(default_factory=dict)


class _BaseCoordinator(DataUpdateCoordinator[None]):
    """Shared auth-aware error handling."""

    config_entry: SleepNumberConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SleepNumberConfigEntry,
        client: AsyncSleepIQ,
        name: str,
        interval,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{entry.data[CONF_USERNAME]}@{DOMAIN}:{name}",
            update_interval=interval,
        )
        self.client = client

    def _reraise(self, err: Exception) -> None:
        """Translate library errors into coordinator outcomes."""
        if isinstance(err, SleepIQLoginException):
            raise ConfigEntryAuthFailed(str(err)) from err
        if isinstance(err, SleepIQTimeoutException):
            raise UpdateFailed(f"Timed out talking to SleepIQ: {err}") from err
        if isinstance(err, SleepIQAPIException):
            if err.code == 401:
                raise ConfigEntryAuthFailed from err
            raise UpdateFailed(f"SleepIQ API error {err.code}: {err}") from err
        raise UpdateFailed(str(err)) from err


class SleepNumberStatusCoordinator(_BaseCoordinator):
    """Live bed-sensor plane: presence, sleep number, pressure (+ foundation if present)."""

    def __init__(self, hass, entry, client) -> None:
        super().__init__(hass, entry, client, "status", STATUS_INTERVAL)

    async def _async_update_data(self) -> None:
        try:
            await self.client.fetch_bed_statuses()
        except (SleepIQLoginException, SleepIQTimeoutException, SleepIQAPIException) as err:
            self._reraise(err)

        # Foundation is optional and may be severed at any time — best-effort only.
        for bed in self.client.beds.values():
            if not bed.foundation.type:
                continue
            try:
                await bed.foundation.update_foundation_status()
            except SleepIQAPIException as err:
                _LOGGER.debug("Foundation status unavailable for %s: %s", bed.name, err)


class SleepNumberSettingsCoordinator(_BaseCoordinator):
    """Slow-changing config: privacy pause and Responsive Air."""

    def __init__(self, hass, entry, client) -> None:
        super().__init__(hass, entry, client, "settings", SETTINGS_INTERVAL)

    async def _async_update_data(self) -> None:
        for bed in self.client.beds.values():
            try:
                await bed.fetch_pause_mode()
            except SleepIQAPIException as err:
                if err.code == 401:
                    self._reraise(err)
                _LOGGER.debug("Pause mode unavailable for %s: %s", bed.name, err)
            try:
                await bed.fetch_responsive_air()
            except SleepIQAPIException as err:
                _LOGGER.debug("Responsive Air unavailable for %s: %s", bed.name, err)


class SleepNumberSleepDataCoordinator(_BaseCoordinator):
    """Nightly sleep-health record (heart rate, respiration, HRV, score)."""

    def __init__(self, hass, entry, client) -> None:
        super().__init__(hass, entry, client, "sleep", SLEEP_DATA_INTERVAL)

    async def _async_update_data(self) -> None:
        tasks = [
            sleeper.fetch_sleep_data()
            for bed in self.client.beds.values()
            for sleeper in bed.sleepers
        ]
        try:
            await asyncio.gather(*tasks)
        except (SleepIQLoginException, SleepIQTimeoutException, SleepIQAPIException) as err:
            self._reraise(err)
