"""BLE transport wiring (setup uses BLE when a bed address is configured)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sleepnumber_pro.bluetooth import BleBridgeClient
from custom_components.sleepnumber_pro.const import (
    CONF_BLE_ADDRESS,
    DOMAIN,
    SOURCE_BLE,
)
from custom_components.sleepnumber_pro.local import LocalStatus


@pytest.fixture
def ble_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="user@example.com",
        data={
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "secret",
            CONF_BLE_ADDRESS: "64:DB:A0:0C:1E:58",
        },
        unique_id="user@example.com",
    )


async def test_ble_transport_and_base_preset(
    hass: HomeAssistant, patched_client, ble_entry
) -> None:
    ble = MagicMock(spec=BleBridgeClient)
    ble.source_name = SOURCE_BLE
    ble.available = AsyncMock(return_value=True)
    ble.status = AsyncMock(
        return_value=LocalStatus(sleep_number_left=44, sleep_number_right=77)
    )
    ble.activate_preset = AsyncMock()

    with patch("custom_components.sleepnumber_pro.BleBridgeClient", return_value=ble):
        ble_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(ble_entry.entry_id)
        await hass.async_block_till_done()

    # Connection reports BLE, sleep number came from the hub over BLE.
    assert hass.states.get("sensor.the_cama_connection").state == SOURCE_BLE
    assert hass.states.get("sensor.the_cama_sean_sleep_number").state == "77"

    # Base-preset select exists (recovers base control the cloud severed).
    sel = "select.the_cama_sean_base_preset"
    assert hass.states.get(sel) is not None

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": sel, "option": "zero_g"},
        blocking=True,
    )
    ble.activate_preset.assert_awaited()  # a foundation command went out over BLE
