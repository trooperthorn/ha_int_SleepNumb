"""MCR (Multi-Channel Radio) binary protocol for Sleep Number BAM hubs over BLE.

This is an independent implementation from the publicly documented protocol
(reverse-engineered by the community from the SleepIQ app; see docs/BLUETOOTH.md
for attribution). Verified against BAM firmware 0.4.1d9 / hardware EVT3 — the same
firmware this project's reference hub reports.

Wire format written to / read from the MCR characteristics:

    [0x16 0x16] + [10-byte header] + [0..15 byte payload] + [CRC16 big-endian]

Header: cmd, target(2), sub(2), status, echo(2), func, (side<<4 | payload_len).
CRC is a Fletcher-16 over header+payload only (not the sync bytes).
"""

from __future__ import annotations

from dataclasses import dataclass

SYNC = bytes([0x16, 0x16])

# Command / status classes (byte 0 and byte 5).
CMD_PUMP = 0x02
CMD_FOUNDATION = 0x42
STATUS_PUMP = 0x02
STATUS_FOUNDATION = 0x42

# Function codes.
FUNC_INIT = 0
FUNC_FORCE_IDLE = 2
FUNC_SET = 17
FUNC_READ = 18
FUNC_PRESET = 21

SIDE_LEFT = 0
SIDE_RIGHT = 1
SIDE_QUERY = 0x0F  # read pump status for both sides

PRESETS = {
    "favorite": 1,
    "read": 2,
    "watch_tv": 3,
    "flat": 4,
    "zero_g": 5,
    "snore": 6,
}


def mcr_crc(data: bytes) -> int:
    """Fletcher-16 style checksum over header+payload."""
    s = r = 0
    for b in data:
        s = (s + b) & 0xFFFF
        r = (r + s) & 0xFFFF
    return r & 0xFFFF


def bed_addr_from_mac(mac: str) -> int:
    """The bed's MCR address is the last two bytes of its BLE MAC."""
    parts = mac.replace("-", ":").split(":")
    return (int(parts[-2], 16) << 8) | int(parts[-1], 16)


def build_frame(
    cmd: int,
    status: int,
    func: int,
    *,
    sub: int = 0x0000,
    target: int = 0x0000,
    echo: int = 0x0000,
    side: int = 0,
    payload: bytes = b"",
) -> bytes:
    """Assemble a complete MCR frame (sync + header + payload + CRC)."""
    if len(payload) > 15:
        raise ValueError("MCR payload max is 15 bytes")
    header = bytes(
        [
            cmd & 0xFF,
            (target >> 8) & 0xFF,
            target & 0xFF,
            (sub >> 8) & 0xFF,
            sub & 0xFF,
            status & 0xFF,
            (echo >> 8) & 0xFF,
            echo & 0xFF,
            func & 0xFF,
            ((side & 0x0F) << 4) | (len(payload) & 0x0F),
        ]
    )
    body = header + payload
    crc = mcr_crc(body)
    return SYNC + body + bytes([(crc >> 8) & 0xFF, crc & 0xFF])


# --- command builders -------------------------------------------------------

def build_init() -> bytes:
    """Handshake that must precede any query (8-byte zero token accepted)."""
    return build_frame(CMD_PUMP, STATUS_PUMP, FUNC_INIT, side=0, payload=bytes(8))


def build_read_pump() -> bytes:
    """Query pump status (sleep numbers + pumping flags)."""
    return build_frame(CMD_PUMP, STATUS_PUMP, FUNC_READ, sub=0, side=SIDE_QUERY)


def build_read_pump_for(bed_addr: int) -> bytes:
    return build_frame(CMD_PUMP, STATUS_PUMP, FUNC_READ, sub=bed_addr, side=SIDE_QUERY)


def build_set_sleep_number(bed_addr: int, side: int, value: int) -> bytes:
    """Set one side's sleep number (0-100)."""
    value = max(0, min(100, int(value)))
    return build_frame(
        CMD_PUMP, STATUS_PUMP, FUNC_SET, sub=bed_addr, side=side,
        payload=bytes([0x00, value]),
    )


def build_foundation_status(bed_addr: int) -> bytes:
    """Query foundation head/foot positions + motion (works over BLE even when
    the cloud reports the foundation as severed)."""
    return build_frame(CMD_FOUNDATION, STATUS_FOUNDATION, FUNC_READ, sub=bed_addr, side=0)


def build_preset(bed_addr: int, side: int, preset: int) -> bytes:
    """Activate a foundation preset (Flat/Zero-G/Snore/...)."""
    return build_frame(
        CMD_FOUNDATION, STATUS_FOUNDATION, FUNC_PRESET, sub=bed_addr, side=side,
        payload=bytes([preset & 0xFF, 0x00]),
    )


# --- response parsing -------------------------------------------------------

@dataclass
class McrResponse:
    func: int          # response function (response bit 0x80 stripped)
    is_response: bool  # whether the response bit was set
    side: int
    payload: bytes


def parse_frame(data: bytes) -> McrResponse | None:
    """Parse a notification frame; returns None if malformed."""
    if len(data) < 14 or data[0:2] != SYNC:
        return None
    body = data[2:-2]
    if len(body) < 10:
        return None
    crc_rx = (data[-2] << 8) | data[-1]
    if mcr_crc(body) != crc_rx:
        return None
    func_raw = body[8]
    side = (body[9] >> 4) & 0x0F
    return McrResponse(
        func=func_raw & 0x7F,
        is_response=bool(func_raw & 0x80),
        side=side,
        payload=body[10:],
    )


@dataclass
class PumpStatus:
    pump_on: bool
    left_sleep_number: int | None
    right_sleep_number: int | None
    left_pumping: bool
    right_pumping: bool


def parse_pump_status(payload: bytes) -> PumpStatus | None:
    """[pump_on, L_SN, R_SN, L_pump, R_pump]."""
    if len(payload) < 3:
        return None
    return PumpStatus(
        pump_on=bool(payload[0]),
        left_sleep_number=payload[1] or None,
        right_sleep_number=payload[2] or None,
        left_pumping=bool(payload[3]) if len(payload) > 3 else False,
        right_pumping=bool(payload[4]) if len(payload) > 4 else False,
    )


@dataclass
class FoundationStatus:
    moving: bool
    head_left: int
    head_right: int
    foot: int
    last_preset: int


def parse_foundation_status(payload: bytes) -> FoundationStatus | None:
    """15-byte foundation readout (func=18, cmd=0x42)."""
    if len(payload) < 5:
        return None
    return FoundationStatus(
        moving=bool(payload[0] & 0x01),
        head_left=payload[1],
        head_right=payload[2],
        foot=payload[3],
        last_preset=payload[14] if len(payload) > 14 else 0,
    )
