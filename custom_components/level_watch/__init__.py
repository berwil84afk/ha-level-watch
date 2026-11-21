"""Level Watch: monitor a water or tank level with trend and thresholds."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .model import LevelWatchModel

PLATFORMS = [Platform.SENSOR]

type LevelWatchConfigEntry = ConfigEntry[LevelWatchModel]


async def async_setup_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> bool:
    model = LevelWatchModel(hass, entry.entry_id, {**entry.data, **entry.options})
    await model.async_load()
    entry.runtime_data = model
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    model.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> None:
    """Delete the stored history together with the entry."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()


async def _async_reload(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
