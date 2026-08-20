"""Config flow for Sleep Number (SleepIQ) Local-First."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .sleepiq_local import AsyncSleepIQ, SleepIQLoginException, SleepIQTimeoutException
from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

_LOGGER = logging.getLogger(__name__)

STEP_USER = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


async def _validate(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Return an error key, or None if the credentials work."""
    client = AsyncSleepIQ(client_session=async_get_clientsession(hass))
    try:
        await client.login(data[CONF_USERNAME], data[CONF_PASSWORD])
    except SleepIQLoginException:
        return "invalid_auth"
    except SleepIQTimeoutException:
        return "cannot_connect"
    return None


class SleepNumberConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect credentials from the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()
            if error := await _validate(self.hass, user_input):
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER,
            errors=errors,
            description_placeholders=self._discovered or None,
        )

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a SleepIQ hub found on the network (MAC 64:DB:A0:*)."""
        # If an account is already configured, the hub is already covered; just
        # record its current address for the local transport (Phase 2) and stop.
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        # A fresh install still needs cloud credentials, so surface the discovered
        # hub address and hand off to the user step.
        self._discovered = {"host": discovery_info.ip}
        return await self.async_step_user()

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauth after an auth failure."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth by re-entering the password."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            data = {
                CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            if error := await _validate(self.hass, data):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(reauth_entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={CONF_USERNAME: reauth_entry.data[CONF_USERNAME]},
        )
