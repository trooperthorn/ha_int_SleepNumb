"""Setup / entity tests for Sleep Number Local-First."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def _setup(hass: HomeAssistant, config_entry) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_unload(hass: HomeAssistant, patched_client, config_entry) -> None:
    """Entry sets up, creates entities, and unloads cleanly."""
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_presence_and_sleep_number(hass: HomeAssistant, patched_client, config_entry) -> None:
    """Live bed-sensor entities reflect the client state."""
    await _setup(hass, config_entry)

    in_bed_sean = hass.states.get("binary_sensor.the_cama_sean_in_bed")
    assert in_bed_sean is not None
    assert in_bed_sean.state == "on"

    in_bed_joanie = hass.states.get("binary_sensor.the_cama_joanie_in_bed")
    assert in_bed_joanie.state == "off"

    sn_sean = hass.states.get("sensor.the_cama_sean_sleep_number")
    assert sn_sean.state == "60"


async def test_sleep_health_sensors(hass: HomeAssistant, patched_client, config_entry) -> None:
    """Nightly biometrics are exposed as sensors."""
    await _setup(hass, config_entry)

    assert hass.states.get("sensor.the_cama_sean_heart_rate").state == "81"
    assert hass.states.get("sensor.the_cama_sean_heart_rate_variability").state == "83"
    assert hass.states.get("sensor.the_cama_joanie_sleep_score").state == "74"


async def test_foundation_severed_does_not_break_setup(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """With the foundation relay cut (type=''), setup still succeeds fully."""
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    # bed-level controls still present
    assert hass.states.get("switch.the_cama_privacy_pause") is not None


async def test_responsive_air_capability(hass: HomeAssistant, patched_client, config_entry) -> None:
    """Responsive Air switch appears because the capability was detected."""
    await _setup(hass, config_entry)
    ra = hass.states.get("switch.the_cama_joanie_responsive_air")
    assert ra is not None
    assert ra.state == "on"  # leftSideEnabled True for Joanie
