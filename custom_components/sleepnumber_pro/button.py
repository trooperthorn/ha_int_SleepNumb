"""Buttons for Sleep Number Local-First: calibrate and stop-pump."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ._compat import AddConfigEntryEntitiesCallback
from .coordinator import SleepNumberConfigEntry
from .entity import bed_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SleepNumberConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up buttons."""
    data = entry.runtime_data
    entities: list[ButtonEntity] = []
    for bed in data.client.beds.values():
        entities.append(CalibrateButton(data.status, bed))
        entities.append(StopPumpButton(data.status, bed))
    async_add_entities(entities)


class _BedButton(CoordinatorEntity, ButtonEntity):
    """Base bed-level button."""

    _attr_has_entity_name = True
    _key = ""

    def __init__(self, coordinator, bed) -> None:
        super().__init__(coordinator)
        self.bed = bed
        self._attr_device_info = bed_device_info(bed)
        self._attr_unique_id = f"{bed.id}_{self._key}"
        self._attr_translation_key = self._key


class CalibrateButton(_BedButton):
    """Recalibrate (baseline) the bed's pressure sensing."""

    _key = "calibrate"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:target"

    async def async_press(self) -> None:
        await self.bed.calibrate()


class StopPumpButton(_BedButton):
    """Force the pump idle, halting any in-progress adjustment."""

    _key = "stop_pump"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:pump-off"

    async def async_press(self) -> None:
        await self.bed.stop_pump()
