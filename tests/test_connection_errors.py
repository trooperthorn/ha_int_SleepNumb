"""Transport failures must never be reported as bad credentials.

Live case (2026-10-09): a DNS timeout during the cloud login was wrapped as
SleepIQLoginException, the coordinator raised ConfigEntryAuthFailed, and Home
Assistant opened a reauth flow against valid credentials.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectorDNSError
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sleepnumber_pro.const import DOMAIN
from custom_components.sleepnumber_pro.sleepiq_local import (
    SleepIQConnectionException,
    SleepIQLoginException,
    SleepIQTimeoutException,
)
from custom_components.sleepnumber_pro.sleepiq_local.api import SleepIQAPI

DNS_ERROR = ClientConnectorDNSError(
    MagicMock(host="ecim.sleepnumber.com", port=443),
    OSError("Timeout while contacting DNS servers"),
)


def _response(status: int = 200, payload: dict | None = None) -> MagicMock:
    """Build an aiohttp-style response usable as ``async with``."""
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=payload or {})
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _raising(exc: BaseException) -> MagicMock:
    """Build a request context manager whose entry raises ``exc``."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=exc)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


# --- library layer ---------------------------------------------------------


async def test_login_dns_failure_is_connection_error() -> None:
    """A DNS failure during the cookie login is a transport error, not a login error."""
    session = MagicMock()
    session.post = MagicMock(return_value=_raising(DNS_ERROR))
    api = SleepIQAPI(client_session=session)

    with pytest.raises(SleepIQConnectionException) as excinfo:
        await api.login("user@example.com", "secret")
    assert not isinstance(excinfo.value, SleepIQLoginException)
    assert excinfo.value.__cause__ is DNS_ERROR


async def test_login_rejected_stays_login_error() -> None:
    """An HTTP 401 on the token endpoint is still a login failure."""
    session = MagicMock()
    session.post = MagicMock(return_value=_response(401))
    api = SleepIQAPI(client_session=session)

    with pytest.raises(SleepIQLoginException, match="Incorrect username or password"):
        await api.login("user@example.com", "secret")


async def test_login_timeout_stays_timeout_error() -> None:
    """A timeout keeps its own type so setup goes to retry, not reauth."""
    session = MagicMock()
    session.post = MagicMock(return_value=_raising(TimeoutError()))
    api = SleepIQAPI(client_session=session)

    with pytest.raises(SleepIQTimeoutException):
        await api.login("user@example.com", "secret")


async def test_request_dns_failure_is_connection_error() -> None:
    """A DNS failure on a data request is surfaced as a transport error."""
    session = MagicMock()
    session.get = MagicMock(return_value=_raising(DNS_ERROR))
    api = SleepIQAPI(client_session=session)
    api.key = "k"

    with pytest.raises(SleepIQConnectionException):
        await api.get("bed")


# --- coordinator layer -----------------------------------------------------


async def test_coordinator_connection_error_is_update_failed(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """A transport failure mid-flight retries; it never demands reauth."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    status = config_entry.runtime_data.status
    patched_client.fetch_bed_statuses = AsyncMock(
        side_effect=SleepIQConnectionException("Connection failure: DNS")
    )
    with pytest.raises(UpdateFailed):
        await status._async_update_data()

    await status.async_refresh()
    await hass.async_block_till_done()
    assert status.last_update_success is False
    assert config_entry.state is ConfigEntryState.LOADED
    assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)


async def test_coordinator_login_error_still_reauths(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """Regression guard: a real credential rejection still raises auth failed."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    status = config_entry.runtime_data.status
    patched_client.fetch_bed_statuses = AsyncMock(
        side_effect=SleepIQLoginException("Incorrect username or password")
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await status._async_update_data()


async def test_settings_coordinator_timeout_is_update_failed(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """A timeout on the pause-mode call is a clean UpdateFailed, not an unexpected error."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    bed = next(iter(patched_client.beds.values()))
    bed.fetch_pause_mode = AsyncMock(side_effect=SleepIQTimeoutException("API call timed out"))
    with pytest.raises(UpdateFailed):
        await config_entry.runtime_data.settings._async_update_data()


# --- setup layer -----------------------------------------------------------


async def test_setup_dns_failure_is_setup_retry(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """A DNS failure at startup goes to setup_retry, never to reauth."""
    patched_client.login = AsyncMock(
        side_effect=SleepIQConnectionException("Connection failure: DNS")
    )
    config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)


async def test_setup_dns_failure_during_init_beds_is_setup_retry(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """The same guard covers the bed discovery call after login."""
    patched_client.init_beds = AsyncMock(
        side_effect=SleepIQConnectionException("Connection failure: DNS")
    )
    config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_login_error_is_setup_error_with_reauth(
    hass: HomeAssistant, patched_client, config_entry
) -> None:
    """Regression guard: a real credential rejection at startup still opens reauth."""
    patched_client.login = AsyncMock(
        side_effect=SleepIQLoginException("Incorrect username or password")
    )
    config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows and flows[0]["context"]["source"] == "reauth"


# --- config flow -----------------------------------------------------------


async def test_user_flow_dns_failure_is_cannot_connect(hass: HomeAssistant, patched_client) -> None:
    """The setup form reports cannot_connect, not invalid_auth, on a transport failure."""
    patched_client.login = AsyncMock(
        side_effect=SleepIQConnectionException("Connection failure: DNS")
    )
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
