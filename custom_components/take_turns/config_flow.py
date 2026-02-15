"""Config flow for Take Turns integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TakeTurnsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Take Turns."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Parse the people list from comma-separated string
            people_str = user_input["people"]
            people = [p.strip() for p in people_str.split(",") if p.strip()]
            
            if len(people) < 2:
                errors["people"] = "need_at_least_two"
            else:
                # Create a unique ID based on the entity_id
                await self.async_set_unique_id(user_input["entity_id"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "entity_id": user_input["entity_id"],
                        "name": user_input["name"],
                        "people": people,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_id"): cv.string,
                    vol.Required("name"): cv.string,
                    vol.Required("people"): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "entity_id_example": "bedtime_story",
                "name_example": "Bedtime Story Reader",
                "people_example": "Mom, Dad, Grandma",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Take Turns."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Parse the people list from comma-separated string
            people_str = user_input["people"]
            people = [p.strip() for p in people_str.split(",") if p.strip()]
            
            if len(people) < 2:
                errors["people"] = "need_at_least_two"
            else:
                # Update the config entry with new data
                return self.async_create_entry(
                    title="",
                    data={
                        "name": user_input["name"],
                        "people": people,
                    },
                )

        # Pre-fill with current values
        current_people = self.config_entry.data.get("people", [])
        people_str = ", ".join(current_people)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name",
                        default=self.config_entry.data.get("name", ""),
                    ): cv.string,
                    vol.Required("people", default=people_str): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "people_example": "Mom, Dad, Grandma",
            },
        )
