"""Local-first transport with cloud fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sleepnumber_pro.const import (
    CONF_LOCAL_HOST,
    DOMAIN,
    SOURCE_CLOUD,
    SOURCE_LOCAL,
)
from custom_components.sleepnumber_pro.local import LocalBridgeClient, LocalStatus


@pytest.fixture
def local_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="user@example.com",
        data={
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "secret",
            CONF_LOCAL_HOST: "192.168.1.159",
        },
        unique_id="user@example.com",
    )


def _fake_local(status_result=None, status_error=None) -> MagicMock:
    # spec against the real HTTP bridge so it has no auto-created `source_name`
    # (the coordinator then resolves the source to "local", as in production).
    client = MagicMock(spec=LocalBridgeClient)
    client.available = AsyncMock(return_value=True)
    if status_error is not None:
        client.status = AsyncMock(side_effect=status_error)
    else:
        client.status = AsyncMock(return_value=status_result)
    return client


async def _setup(hass, entry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_local_preferred(hass: HomeAssistant, patched_client, local_entry) -> None:
    """When the bridge answers, presence/sleep number come from the hub."""
    local = _fake_local(
        LocalStatus(
            sleep_number_left=44,
            sleep_number_right=77,
            in_bed_left=True,
            in_bed_right=False,
        )
    )
    with patch("custom_components.sleepnumber_pro.LocalBridgeClient", return_value=local):
        await _setup(hass, local_entry)

    assert hass.states.get("sensor.the_cama_connection").state == SOURCE_LOCAL
    # Joanie is the LEFT sleeper, Sean the RIGHT.
    assert hass.states.get("binary_sensor.the_cama_joanie_in_bed").state == "on"
    assert hass.states.get("sensor.the_cama_sean_sleep_number").state == "77"


async def test_falls_back_to_cloud(hass: HomeAssistant, patched_client, local_entry) -> None:
    """If the bridge errors during a refresh, the cloud serves that cycle."""
    local = _fake_local(status_error=aiohttp.ClientError("bridge down"))
    with patch("custom_components.sleepnumber_pro.LocalBridgeClient", return_value=local):
        await _setup(hass, local_entry)

    assert hass.states.get("sensor.the_cama_connection").state == SOURCE_CLOUD
    # Cloud fixture values remain (Sean right = 60).
    assert hass.states.get("sensor.the_cama_sean_sleep_number").state == "60"
