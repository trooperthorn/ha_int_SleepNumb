"""Unit tests for the MCR BLE protocol codec, checked against documented vectors."""

from __future__ import annotations

from custom_components.sleepnumber_pro import mcr


def test_crc_init_vector():
    # Documented init frame: header+payload CRC must be 0x0086.
    body = bytes.fromhex("02000000000200000008" + "0000000000000000")
    assert mcr.mcr_crc(body) == 0x0086


def test_build_init_matches_reference_hex():
    assert (
        mcr.build_init().hex()
        == "16160200000000020000000800000000000000000086"
    )


def test_bed_addr_from_mac():
    assert mcr.bed_addr_from_mac("64:DB:A0:0C:1E:58") == 0x1E58
    assert mcr.bed_addr_from_mac("64-db-a0-07-dd-02") == 0xDD02


def test_frame_roundtrip():
    frame = mcr.build_set_sleep_number(0x1E58, mcr.SIDE_RIGHT, 55)
    parsed = mcr.parse_frame(frame)
    assert parsed is not None
    assert parsed.func == mcr.FUNC_SET
    assert parsed.side == mcr.SIDE_RIGHT
    assert parsed.payload == bytes([0x00, 55])


def test_sleep_number_clamped():
    frame = mcr.build_set_sleep_number(0x1E58, mcr.SIDE_LEFT, 250)
    assert mcr.parse_frame(frame).payload[1] == 100


def test_frame_structure():
    frame = mcr.build_foundation_status(0x1E58)
    assert frame[:2] == mcr.SYNC
    body = frame[2:-2]
    assert body[0] == mcr.CMD_FOUNDATION  # cmd
    assert body[5] == mcr.STATUS_FOUNDATION  # status
    assert body[3] == 0x1E and body[4] == 0x58  # sub = bed addr
    assert body[8] == mcr.FUNC_READ


def test_parse_pump_status():
    st = mcr.parse_pump_status(bytes([1, 35, 60, 0, 0]))
    assert st.pump_on is True
    assert st.left_sleep_number == 35
    assert st.right_sleep_number == 60
    assert st.left_pumping is False


def test_parse_foundation_status():
    payload = bytes([0x43, 40, 55, 20, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x05])
    st = mcr.parse_foundation_status(payload)
    assert st.moving is True  # 0x43 -> bit 0 set
    assert st.head_left == 40 and st.head_right == 55 and st.foot == 20
    assert st.last_preset == 0x05


def test_preset_frame():
    frame = mcr.build_preset(0x1E58, mcr.SIDE_LEFT, mcr.PRESETS["zero_g"])
    p = mcr.parse_frame(frame)
    assert p.func == mcr.FUNC_PRESET
    assert p.payload[0] == 5


def test_parse_rejects_garbage():
    assert mcr.parse_frame(b"\x00\x01\x02") is None
    # Non-zero body with a zeroed CRC field -> checksum mismatch -> rejected.
    assert mcr.parse_frame(mcr.SYNC + bytes([1]) + bytes(11)) is None
