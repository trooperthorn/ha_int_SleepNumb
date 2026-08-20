"""BLE transport for Sleep Number BAM hubs (MCR protocol).

The hub carries its own BLE radio, so this is the no-root local path: reach the
bed over Bluetooth (a local adapter or an ESPHome Bluetooth Proxy) and speak the
MCR binary protocol directly. Crucially, the foundation/base — which the cloud
now reports as "No Foundation Device" — is fully reachable here, so BLE recovers
base control the cloud severed.

Exposes the same ``available()`` / ``status()`` surface as the HTTP bridge so the
coordinator can prefer it identically, plus control methods for firmness and
foundation presets.
"""

from __future__ import annotations

import asyncio
import logging

from .const import SOURCE_BLE
from .local import LocalStatus
from . import mcr

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "ffffd1fd-388d-938b-344a-939d1f6efee0"
TX_UUID = "ffffd1fd-388d-938b-344a-939d1f6efee1"  # notify: bed -> us
RX_UUID = "ffffd1fd-388d-938b-344a-939d1f6efee2"  # write:  us -> bed

RESPONSE_TIMEOUT = 6.0


class BleBridgeClient:
    """Connect-on-demand MCR client over BLE."""

    source_name = SOURCE_BLE

    def __init__(self, hass, address: str) -> None:
        self.hass = hass
        self.address = address
        self.bed_addr = mcr.bed_addr_from_mac(address)
        self._lock = asyncio.Lock()

    # -- discovery -----------------------------------------------------------

    def _ble_device(self):
        """Resolve a connectable BLEDevice via HA's Bluetooth stack, or None."""
        from homeassistant.components import bluetooth

        return bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )

    async def available(self) -> bool:
        return self._ble_device() is not None

    # -- transaction ---------------------------------------------------------

    async def _run(self, queries: list[tuple[bytes, int]]) -> dict[int, bytes]:
        """Connect, handshake, send each (frame, expected_func) query, and return
        {func: payload} for the responses seen. Serialised by a lock so we never
        hold two GATT connections (an ESP32 proxy allows only one)."""
        from bleak_retry_connector import establish_connection

        device = self._ble_device()
        if device is None:
            raise BleUnavailable(f"{self.address} not in range / no proxy")

        async with self._lock:
            buffer = bytearray()
            responses: dict[int, bytes] = {}
            waiting_for: set[int] = set()
            event = asyncio.Event()

            def _on_notify(_char, data: bytearray) -> None:
                buffer.extend(data)
                # Extract complete frames (payload length lives in header byte 9).
                while len(buffer) >= 14 and buffer[0:2] == mcr.SYNC:
                    payload_len = buffer[11] & 0x0F
                    total = 2 + 10 + payload_len + 2
                    if len(buffer) < total:
                        break
                    frame = bytes(buffer[:total])
                    del buffer[:total]
                    parsed = mcr.parse_frame(frame)
                    if parsed is not None:
                        responses[parsed.func] = parsed.payload
                        if parsed.func in waiting_for:
                            event.set()

            client = await establish_connection(
                __import__("bleak").BleakClient, device, self.address
            )
            try:
                await client.start_notify(TX_UUID, _on_notify)
                # Handshake first; the bed ignores queries without it.
                await client.write_gatt_char(RX_UUID, mcr.build_init(), response=True)
                await asyncio.sleep(0.2)
                for frame, expect_func in queries:
                    waiting_for = {expect_func}
                    event.clear()
                    # Proxy quirk: MCR RX must be written WITH response.
                    await client.write_gatt_char(RX_UUID, frame, response=True)
                    try:
                        await asyncio.wait_for(event.wait(), RESPONSE_TIMEOUT)
                    except TimeoutError:
                        _LOGGER.debug("No BLE response for func %s", expect_func)
                return responses
            finally:
                try:
                    await client.stop_notify(TX_UUID)
                except Exception:  # noqa: BLE001
                    pass
                await client.disconnect()

    # -- reads ---------------------------------------------------------------

    async def status(self) -> LocalStatus:
        """Read sleep numbers over BLE. (Presence is broken in MCR firmware, so it
        stays None here and is filled from the cloud/pressure plane.)"""
        responses = await self._run(
            [(mcr.build_read_pump_for(self.bed_addr), mcr.FUNC_READ)]
        )
        pump = mcr.parse_pump_status(responses.get(mcr.FUNC_READ, b""))
        if pump is None:
            raise BleUnavailable("no pump status")
        return LocalStatus(
            sleep_number_left=pump.left_sleep_number,
            sleep_number_right=pump.right_sleep_number,
        )

    async def foundation_status(self):
        responses = await self._run(
            [(mcr.build_foundation_status(self.bed_addr), mcr.FUNC_READ)]
        )
        return mcr.parse_foundation_status(responses.get(mcr.FUNC_READ, b""))

    # -- writes --------------------------------------------------------------

    async def set_sleep_number(self, side: int, value: int) -> None:
        await self._run([(mcr.build_set_sleep_number(self.bed_addr, side, value), mcr.FUNC_SET)])

    async def activate_preset(self, side: int, preset: int) -> None:
        await self._run([(mcr.build_preset(self.bed_addr, side, preset), mcr.FUNC_PRESET)])


class BleUnavailable(Exception):
    """Raised when the bed cannot be reached over BLE."""
