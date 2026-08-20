"""The Sleep Number (SleepIQ) Local-First integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .sleepiq_local import (
    AsyncSleepIQ,
    SleepIQAPIException,
    SleepIQLoginException,
    SleepIQTimeoutException,
)
from .coordinator import (
    SleepNumberConfigEntry,
    SleepNumberData,
    SleepNumberSettingsCoordinator,
    SleepNumberSleepDataCoordinator,
    SleepNumberStatusCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SleepNumberConfigEntry) -> bool:
    """Set up Sleep Number Local-First from a config entry."""
    session = async_create_clientsession(hass)
    client = AsyncSleepIQ(client_session=session)

    try:
        await client.login(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    except SleepIQLoginException as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except SleepIQTimeoutException as err:
        raise ConfigEntryNotReady(str(err) or "Timed out during authentication") from err

    try:
        await client.init_beds()
    except SleepIQTimeoutException as err:
        raise ConfigEntryNotReady(str(err) or "Timed out during initialization") from err
    except SleepIQAPIException as err:
        raise ConfigEntryNotReady(str(err) or "Error reading from SleepIQ") from err

    # Discover which subsystems are actually reachable right now, so platforms
    # only create entities for capabilities the cloud still serves.
    capabilities = {
        "foundation": any(bed.foundation.type for bed in client.beds.values()),
        "responsive_air": False,
    }
    for bed in client.beds.values():
        try:
            await bed.fetch_responsive_air()
            if bed.responsive_air:
                capabilities["responsive_air"] = True
        except SleepIQAPIException as err:
            _LOGGER.debug("Responsive Air not available for %s: %s", bed.name, err)

    status = SleepNumberStatusCoordinator(hass, entry, client)
    settings = SleepNumberSettingsCoordinator(hass, entry, client)
    sleep = SleepNumberSleepDataCoordinator(hass, entry, client)

    await status.async_config_entry_first_refresh()
    await settings.async_config_entry_first_refresh()
    await sleep.async_config_entry_first_refresh()

    entry.runtime_data = SleepNumberData(
        client=client,
        status=status,
        settings=settings,
        sleep=sleep,
        capabilities=capabilities,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SleepNumberConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
