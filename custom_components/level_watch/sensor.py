"""Sensors of Level Watch."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LevelWatchConfigEntry
from .const import DOMAIN, QUALITIES, QUALITY_NO_DATA, TRENDS, UNIT_RATE, VERSION
from .model import LevelWatchModel, Snapshot

PARALLEL_UPDATES = 0

TREND_ICONS = {
    "rising": "mdi:trending-up",
    "falling": "mdi:trending-down",
    "stable": "mdi:trending-neutral",
}


@dataclass(frozen=True, kw_only=True)
class LevelSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Snapshot], Any]
    attrs_fn: Callable[[LevelWatchModel], dict[str, Any]] | None = None
    # Shown even while the source has no data (the quality sensor).
    always_available: bool = False


def _level_attrs(model: LevelWatchModel) -> dict[str, Any]:
    snap = model.snapshot
    return {
        "raw_level": None if snap.raw_level is None else round(snap.raw_level, 2),
        "source_entity": model.settings.source,
        "kind": model.settings.kind,
        "reference_min": model.settings.ref_min,
        "reference_max": model.settings.ref_max,
    }


LENGTH_COMMON = {
    "device_class": SensorDeviceClass.DISTANCE,
    "native_unit_of_measurement": UnitOfLength.CENTIMETERS,
    "suggested_display_precision": 1,
}

SENSORS: tuple[LevelSensorDescription, ...] = (
    LevelSensorDescription(
        key="level",
        translation_key="level",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.level,
        attrs_fn=_level_attrs,
        **LENGTH_COMMON,
    ),
    LevelSensorDescription(
        key="percent",
        translation_key="percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda s: s.percent,
    ),
    LevelSensorDescription(
        key="trend",
        translation_key="trend",
        device_class=SensorDeviceClass.ENUM,
        options=TRENDS,
        value_fn=lambda s: s.trend,
    ),
    LevelSensorDescription(
        key="rate",
        translation_key="rate",
        native_unit_of_measurement=UNIT_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda s: s.rate,
    ),
    LevelSensorDescription(
        key="min_24h",
        translation_key="min_24h",
        value_fn=lambda s: s.min_24h,
        **LENGTH_COMMON,
    ),
    LevelSensorDescription(
        key="max_24h",
        translation_key="max_24h",
        value_fn=lambda s: s.max_24h,
        **LENGTH_COMMON,
    ),
    LevelSensorDescription(
        key="change_24h",
        translation_key="change_24h",
        value_fn=lambda s: s.change_24h,
        **LENGTH_COMMON,
    ),
    LevelSensorDescription(
        key="data_quality",
        translation_key="data_quality",
        device_class=SensorDeviceClass.ENUM,
        options=QUALITIES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.quality,
        attrs_fn=lambda m: {"last_reading": m.snapshot.last_reading},
        always_available=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LevelWatchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    model = entry.runtime_data
    descriptions = [
        d
        for d in SENSORS
        if d.key != "percent" or model.settings.ref_max is not None
    ]
    async_add_entities(LevelSensor(entry, model, d) for d in descriptions)


class LevelSensor(SensorEntity):
    """One derived value of a monitored level."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: LevelSensorDescription

    def __init__(
        self,
        entry: LevelWatchConfigEntry,
        model: LevelWatchModel,
        description: LevelSensorDescription,
    ) -> None:
        self.entity_description = description
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Level Watch",
            model="Water level" if model.settings.kind == "water" else "Tank",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._model.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        if self.entity_description.always_available:
            return True
        return self._model.snapshot.quality != QUALITY_NO_DATA

    @property
    def native_value(self) -> Any:
        value = self.entity_description.value_fn(self._model.snapshot)
        if isinstance(value, float):
            return round(value, 3)
        return value

    @property
    def icon(self) -> str | None:
        if self.entity_description.key == "trend":
            return TREND_ICONS.get(self._model.snapshot.trend or "", "mdi:help")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self._model)
