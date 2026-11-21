"""One binary sensor per threshold: on while the threshold is reached."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LevelWatchConfigEntry
from .const import QUALITY_NO_DATA
from .entity import LevelWatchEntity
from .model import LevelWatchModel
from .thresholds import ABOVE, Threshold

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LevelWatchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    model = entry.runtime_data
    async_add_entities(
        ThresholdSensor(entry, model, th) for th in model.settings.thresholds
    )


class ThresholdSensor(LevelWatchEntity, BinarySensorEntity):
    """On while the level is beyond the threshold."""

    def __init__(
        self, entry: LevelWatchConfigEntry, model: LevelWatchModel, threshold: Threshold
    ) -> None:
        super().__init__(entry, model, f"threshold_{threshold.id}")
        self._threshold = threshold
        self._attr_name = threshold.name
        self._attr_icon = (
            "mdi:arrow-collapse-up" if threshold.direction == ABOVE else "mdi:arrow-collapse-down"
        )

    @property
    def available(self) -> bool:
        return self._model.snapshot.quality != QUALITY_NO_DATA

    @property
    def is_on(self) -> bool | None:
        active = self._model.snapshot.active or {}
        return active.get(self._threshold.id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        th = self._threshold
        return {
            "value": th.value,
            "direction": th.direction,
            "hysteresis": th.hysteresis,
            "color": th.hex_color,
            "notify": th.notify,
        }
