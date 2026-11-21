"""Base entity shared by the Level Watch platforms."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, KIND_WATER, VERSION
from .model import LevelWatchModel


class LevelWatchEntity(Entity):
    """Belongs to the entry's device and updates with the model."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, model: LevelWatchModel, key: str) -> None:
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        model.unique_ids.add(self._attr_unique_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Level Watch",
            model="Water level" if model.settings.kind == KIND_WATER else "Tank",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._model.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
