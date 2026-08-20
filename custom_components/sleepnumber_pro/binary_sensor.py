"""Presence (in-bed) binary sensors for Sleep Number Local-First."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from ._compat import AddConfigEntryEntitiesCallback

from .const import ICON_EMPTY, ICON_OCCUPIED, IS_IN_BED
from .coordinator import SleepNumberConfigEntry
from .entity import SleepNumberSleeperEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SleepNumberConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up presence sensors."""
    data = entry.runtime_data
    async_add_entities(
        InBedBinarySensor(data.status, bed, sleeper)
        for bed in data.client.beds.values()
        for sleeper in bed.sleepers
    )


class InBedBinarySensor(SleepNumberSleeperEntity, BinarySensorEntity):
    """Whether a sleeper is currently in bed."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator, bed, sleeper) -> None:
        super().__init__(coordinator, bed, sleeper, IS_IN_BED)

    @callback
    def _async_update_attrs(self) -> None:
        self._attr_is_on = self.sleeper.in_bed
        self._attr_icon = ICON_OCCUPIED if self.sleeper.in_bed else ICON_EMPTY
