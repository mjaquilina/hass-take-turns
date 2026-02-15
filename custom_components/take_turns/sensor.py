"""Sensor platform for Take Turns integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Take Turns sensor from a config entry."""
    entity_id = config_entry.data["entity_id"]
    
    # Use options if available, otherwise use data
    people_list = config_entry.options.get("people", config_entry.data["people"])
    name = config_entry.options.get("name", config_entry.data["name"])
    
    # Get current index from storage
    store = hass.data[DOMAIN]["store"]
    stored_state = await store.async_load() or {}
    current_index = stored_state.get(entity_id, {}).get("current_index", 0)
    
    # Validate index
    if current_index >= len(people_list):
        current_index = 0
    
    # Create sensor entity
    sensor = TakeTurnsSensor(
        entity_id=entity_id,
        name=name,
        people=people_list,
        current_index=current_index,
        entry_id=config_entry.entry_id,
    )
    
    async_add_entities([sensor], update_before_add=True)


class TakeTurnsSensor(SensorEntity):
    """Representation of a Take Turns sensor."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        people: list[str],
        current_index: int,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._entity_id = entity_id
        self._attr_name = name
        self._people = people
        self._current_index = current_index
        self._attr_unique_id = f"{DOMAIN}_{entity_id}"
        self.entity_id = f"sensor.{entity_id}"
        self._entry_id = entry_id

    @property
    def native_value(self) -> str:
        """Return the current person."""
        return self._people[self._current_index]

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "people": self._people,
            "current_index": self._current_index,
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:account-multiple"

    def set_next(self) -> None:
        """Move to the next person."""
        self._current_index = (self._current_index + 1) % len(self._people)
        self.async_write_ha_state()

    def set_person(self, person: str) -> None:
        """Set a specific person as current."""
        try:
            self._current_index = self._people.index(person)
            self.async_write_ha_state()
        except ValueError:
            _LOGGER.error(
                f"Person '{person}' not found. Available: {self._people}"
            )

    def update_config(self, name: str, people: list[str]) -> None:
        """Update configuration from options flow."""
        self._attr_name = name
        old_person = self._people[self._current_index] if self._current_index < len(self._people) else None
        self._people = people
        
        # Try to maintain the same person if they still exist
        if old_person and old_person in people:
            self._current_index = people.index(old_person)
        elif self._current_index >= len(people):
            self._current_index = 0
        
        self.async_write_ha_state()

    @property
    def current_index(self) -> int:
        """Return current index (for saving state)."""
        return self._current_index
