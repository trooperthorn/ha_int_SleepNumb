"""Shared fixtures for Sleep Number Local-First tests.

Mirrors the Windows compatibility handling proven out in the sibling Bond
integration: force a selector loop for aiodns and relax pytest-socket to
loopback-only so the HA event loop can build its self-pipe on Windows.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_socket

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

if sys.platform == "win32":

    def _disable_socket_loopback_ok(allow_unix_socket: bool = False) -> None:
        pytest_socket.enable_socket()
        pytest_socket.socket_allow_hosts(["127.0.0.1", "::1"], allow_unix_socket=True)

    pytest_socket.disable_socket = _disable_socket_loopback_ok

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.sleepnumber_pro.const import DOMAIN  # noqa: E402
from custom_components.sleepnumber_pro.sleepiq_local import SleepIQBed  # noqa: E402
from custom_components.sleepnumber_pro.sleepiq_local.consts import Side  # noqa: E402
from custom_components.sleepnumber_pro.sleepiq_local.sleeper import SleepData  # noqa: E402


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


@pytest.fixture(autouse=True)
def _stub_client_session():
    """Avoid building a real aiohttp session (aiodns needs a selector loop on
    Windows). The API client is mocked, so the session is never actually used.
    """
    fake = MagicMock()
    with (
        patch(
            "custom_components.sleepnumber_pro.async_create_clientsession",
            return_value=fake,
        ),
        patch(
            "custom_components.sleepnumber_pro.config_flow.async_get_clientsession",
            return_value=fake,
        ),
    ):
        yield


BED_DATA = {
    "name": "The Cama",
    "bedId": "bed-1",
    "accountId": "acct-1",
    "macAddress": "64DBA00C1E58",
    "model": "P6",
    "generation": "360",
    "sleeperLeftId": "sleeper-L",
    "sleeperRightId": "sleeper-R",
}


def _build_bed() -> SleepIQBed:
    """Build a real SleepIQBed with a stub API and live-ish values set."""
    api = MagicMock()
    bed = SleepIQBed(api, BED_DATA)
    bed.foundation.type = ""  # foundation severed by the cloud (the real case)
    bed.paused = False
    bed.responsive_air = {"leftSideEnabled": True, "rightSideEnabled": False}
    left, right = bed.sleepers[0], bed.sleepers[1]
    left.name, left.side = "Joanie", Side.LEFT
    left.in_bed, left.sleep_number, left.pressure = False, 35, 1361
    left.sleep_data = SleepData(sleep_score=74, heart_rate=67, respiratory_rate=16, hrv=184, duration=40443)
    right.name, right.side = "Sean", Side.RIGHT
    right.in_bed, right.sleep_number, right.pressure = True, 60, 2402
    right.sleep_data = SleepData(sleep_score=62, heart_rate=81, respiratory_rate=12, hrv=83, duration=19665)
    # side_full is derived in __init__; refresh after overriding side
    from custom_components.sleepnumber_pro.sleepiq_local.consts import SIDES_FULL
    left.side_full = SIDES_FULL[Side.LEFT]
    right.side_full = SIDES_FULL[Side.RIGHT]

    # Stub network methods so fixtures are fully offline and keep the values above.
    bed.fetch_pause_mode = AsyncMock()
    bed.fetch_responsive_air = AsyncMock()
    bed.set_pause_mode = AsyncMock()
    bed.set_responsive_air = AsyncMock()
    bed.calibrate = AsyncMock()
    bed.stop_pump = AsyncMock()
    for sleeper in bed.sleepers:
        sleeper.fetch_sleep_data = AsyncMock()
        sleeper.set_sleepnumber = AsyncMock()
    return bed


@pytest.fixture
def mock_client() -> MagicMock:
    """A mocked AsyncSleepIQ with one populated bed and no network I/O."""
    client = MagicMock()
    bed = _build_bed()
    client.beds = {bed.id: bed}
    client.login = AsyncMock()
    client.init_beds = AsyncMock()
    client.fetch_bed_statuses = AsyncMock()
    return client


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A config entry for the integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
        unique_id="user@example.com",
    )


@pytest.fixture
def patched_client(mock_client):
    """Patch AsyncSleepIQ everywhere the integration constructs it."""
    with (
        patch("custom_components.sleepnumber_pro.AsyncSleepIQ", return_value=mock_client),
        patch("custom_components.sleepnumber_pro.config_flow.AsyncSleepIQ", return_value=mock_client),
    ):
        yield mock_client
