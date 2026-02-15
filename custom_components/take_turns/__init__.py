"""The Take Turns integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
import voluptuous as vol

from .const import DOMAIN, STORAGE_VERSION, STORAGE_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                cv.slug: vol.Schema(
                    {
                        vol.Required("people"): vol.All(cv.ensure_list, [cv.string]),
                        vol.Optional("name"): cv.string,
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Take Turns component from YAML."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize storage if not already done
    if "store" not in hass.data[DOMAIN]:
        store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        hass.data[DOMAIN]["store"] = store
        hass.data[DOMAIN]["entities"] = {}
        
        # Register services once
        await _register_services(hass)
    
    # Handle YAML configuration
    if DOMAIN in config:
        store = hass.data[DOMAIN]["store"]
        stored_state = await store.async_load() or {}
        
        for entity_id, entity_config in config[DOMAIN].items():
            people_list = entity_config["people"]
            name = entity_config.get("name", entity_id.replace("_", " ").title())
            
            # Load saved index or start at 0
            current_index = stored_state.get(entity_id, {}).get("current_index", 0)
            
            # Validate index is still valid for current people list
            if current_index >= len(people_list):
                current_index = 0
            
            hass.data[DOMAIN]["entities"][entity_id] = {
                "people": people_list,
                "name": name,
                "current_index": current_index,
                "source": "yaml",
            }
            
            # Initialize sensor state
            sensor_entity_id = f"sensor.{entity_id}"
            hass.states.async_set(
                sensor_entity_id,
                people_list[current_index],
                {
                    "people": people_list,
                    "current_index": current_index,
                    "friendly_name": name,
                }
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry (UI configuration)."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize storage if not already done
    if "store" not in hass.data[DOMAIN]:
        store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        hass.data[DOMAIN]["store"] = store
        hass.data[DOMAIN]["entities"] = {}
        
        # Register services once
        await _register_services(hass)
    
    entity_id = entry.data["entity_id"]
    
    # Track this config entry
    hass.data[DOMAIN]["entities"][entity_id] = {
        "source": "config_entry",
        "entry_id": entry.entry_id,
    }
    
    # Set up the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Update options."""
    # Reload the config entry to update the sensor
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    entity_id = entry.data["entity_id"]
    
    # Remove entity from tracking
    if entity_id in hass.data[DOMAIN]["entities"]:
        del hass.data[DOMAIN]["entities"][entity_id]
    
    # Unload the sensor platform
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove a config entry."""
    entity_id = entry.data["entity_id"]
    
    # Remove from storage
    store = hass.data[DOMAIN]["store"]
    stored_state = await store.async_load() or {}
    if entity_id in stored_state:
        del stored_state[entity_id]
        await store.async_save(stored_state)


async def _register_services(hass: HomeAssistant):
    """Register services for the integration."""
    
    async def save_state():
        """Save current state to storage."""
        store = hass.data[DOMAIN]["store"]
        state_to_save = {}
        for entity_id, data in hass.data[DOMAIN]["entities"].items():
            state_to_save[entity_id] = {
                "current_index": data["current_index"]
            }
        await store.async_save(state_to_save)

    async def handle_next_turn(call: ServiceCall):
        """Handle the next_turn service call."""
        entity_id_input = call.data.get("entity_id")
        
        if not entity_id_input:
            _LOGGER.error("No entity_id provided in service call")
            return
        
        # Strip 'sensor.' prefix if present to get the base entity_id
        if entity_id_input.startswith("sensor."):
            base_entity_id = entity_id_input[7:]
        else:
            base_entity_id = entity_id_input
        
        sensor_entity_id = f"sensor.{base_entity_id}"
        
        # Try to get the sensor entity  
        try:
            # Call service on the sensor entity
            await hass.services.async_call(
                "homeassistant",
                "update_entity",
                {"entity_id": sensor_entity_id},
                blocking=False,
            )
        except Exception:
            pass
        
        # Get entity from component
        if "sensor" in hass.data.get("entity_components", {}):
            component = hass.data["entity_components"]["sensor"]
            entity = component.get_entity(sensor_entity_id)
            
            if entity and hasattr(entity, "set_next"):
                entity.set_next()
                # Save state
                store = hass.data[DOMAIN]["store"]
                stored_state = await store.async_load() or {}
                stored_state[base_entity_id] = {"current_index": entity.current_index}
                await store.async_save(stored_state)
                return
        
        # Fallback for YAML entities
        if base_entity_id in hass.data[DOMAIN]["entities"]:
            data = hass.data[DOMAIN]["entities"][base_entity_id]
            if data.get("source") == "yaml":
                current_index = data["current_index"]
                people_list = data["people"]
                
                next_index = (current_index + 1) % len(people_list)
                data["current_index"] = next_index
                
                hass.states.async_set(
                    sensor_entity_id,
                    people_list[next_index],
                    {
                        "people": people_list,
                        "current_index": next_index,
                        "friendly_name": data["name"],
                    }
                )
                
                store = hass.data[DOMAIN]["store"]
                stored_state = await store.async_load() or {}
                stored_state[base_entity_id] = {"current_index": next_index}
                await store.async_save(stored_state)
                return
        
        available_entities = list(hass.data[DOMAIN]["entities"].keys())
        _LOGGER.error(
            f"Entity '{base_entity_id}' not found. Available entities: {available_entities}"
        )

    async def handle_set_person(call: ServiceCall):
        """Handle the set_person service call."""
        entity_id_input = call.data.get("entity_id")
        person = call.data.get("person")
        
        if not entity_id_input:
            _LOGGER.error("No entity_id provided in service call")
            return
        
        if not person:
            _LOGGER.error("No person provided in service call")
            return
        
        # Strip 'sensor.' prefix if present
        if entity_id_input.startswith("sensor."):
            base_entity_id = entity_id_input[7:]
        else:
            base_entity_id = entity_id_input
        
        sensor_entity_id = f"sensor.{base_entity_id}"
        
        # Try to get the sensor entity
        if "sensor" in hass.data.get("entity_components", {}):
            component = hass.data["entity_components"]["sensor"]
            entity = component.get_entity(sensor_entity_id)
            
            if entity and hasattr(entity, "set_person"):
                entity.set_person(person)
                # Save state
                store = hass.data[DOMAIN]["store"]
                stored_state = await store.async_load() or {}
                stored_state[base_entity_id] = {"current_index": entity.current_index}
                await store.async_save(stored_state)
                return
        
        # Fallback for YAML entities
        if base_entity_id in hass.data[DOMAIN]["entities"]:
            data = hass.data[DOMAIN]["entities"][base_entity_id]
            if data.get("source") == "yaml":
                people_list = data["people"]
                
                try:
                    new_index = people_list.index(person)
                except ValueError:
                    _LOGGER.error(
                        f"Person '{person}' not found in {base_entity_id}. Available people: {people_list}"
                    )
                    return
                
                data["current_index"] = new_index
                
                hass.states.async_set(
                    sensor_entity_id,
                    people_list[new_index],
                    {
                        "people": people_list,
                        "current_index": new_index,
                        "friendly_name": data["name"],
                    }
                )
                
                store = hass.data[DOMAIN]["store"]
                stored_state = await store.async_load() or {}
                stored_state[base_entity_id] = {"current_index": new_index}
                await store.async_save(stored_state)
                return
        
        available_entities = list(hass.data[DOMAIN]["entities"].keys())
        _LOGGER.error(
            f"Entity '{base_entity_id}' not found. Available entities: {available_entities}"
        )

    # Register services (only once)
    if not hass.services.has_service(DOMAIN, "next_turn"):
        hass.services.async_register(
            DOMAIN,
            "next_turn",
            handle_next_turn,
            schema=vol.Schema({
                vol.Required("entity_id"): cv.string,
            })
        )

    if not hass.services.has_service(DOMAIN, "set_person"):
        hass.services.async_register(
            DOMAIN,
            "set_person",
            handle_set_person,
            schema=vol.Schema({
                vol.Required("entity_id"): cv.string,
                vol.Required("person"): cv.string,
            })
        )

