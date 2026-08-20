"""Base entities for Sleep Number (SleepIQ) Local-First."""

from __future__ import annotations

from abc import abstractmethod

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .sleepiq_local import SleepIQBed, SleepIQSleeper
from .const import DOMAIN, MANUFACTURER


def bed_device_info(bed: SleepIQBed) -> DeviceInfo:
    """Device for the bed / SleepIQ hub."""
    return DeviceInfo(
        identifiers={(DOMAIN, bed.id)},
        connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(bed.mac_addr))},
        manufacturer=MANUFACTURER,
        name=bed.name,
        model=bed.model,
    )


def sleeper_device_info(bed: SleepIQBed, sleeper: SleepIQSleeper) -> DeviceInfo:
    """Device for one sleeper (a side of the bed), linked to the bed hub."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{bed.id}_{sleeper.sleeper_id}")},
        manufacturer=MANUFACTURER,
        name=f"{bed.name} {sleeper.name}",
        model=f"{bed.model} side",
        via_device=(DOMAIN, bed.id),
    )


class SleepNumberBedEntity(CoordinatorEntity):
    """Entity attached to the bed hub device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, bed: SleepIQBed) -> None:
        super().__init__(coordinator)
        self.bed = bed
        self._attr_device_info = bed_device_info(bed)
        self._async_update_attrs()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    @abstractmethod
    def _async_update_attrs(self) -> None:
        """Refresh cached attributes from the library objects."""


class SleepNumberSleeperEntity(SleepNumberBedEntity):
    """Entity attached to a single sleeper device."""

    def __init__(self, coordinator, bed: SleepIQBed, sleeper: SleepIQSleeper, key: str) -> None:
        self.sleeper = sleeper
        super().__init__(coordinator, bed)
        self._attr_device_info = sleeper_device_info(bed, sleeper)
        self._attr_unique_id = f"{sleeper.sleeper_id}_{key}"
        self._attr_translation_key = key
