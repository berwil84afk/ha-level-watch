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
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LevelWatchConfigEntry
from .const import QUALITIES, QUALITY_NO_DATA, TRENDS, UNIT_RATE
from .entity import LevelWatchEntity
from .model import LevelWatchModel, Snapshot
from .thresholds import NORMAL_COLOR

PARALLEL_UPDATES = 0

STAGE_NORMAL = "Normal"

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


def _color(model: LevelWatchModel) -> str:
    stage = model.snapshot.stage
    return stage.hex_color if stage else NORMAL_COLOR


def _level_attrs(model: LevelWatchModel) -> dict[str, Any]:
    """Everything a card needs to draw the level with its thresholds."""
    snap = model.snapshot
    s = model.settings
    active = snap.active or {}
    return {
        "raw_level": None if snap.raw_level is None else round(snap.raw_level, 2),
        "source_entity": s.source,
        "kind": s.kind,
        "reference_min": s.ref_min,
        "reference_max": s.ref_max,
        "color": _color(model),
        "stage": snap.stage.name if snap.stage else None,
        "thresholds": [
            {
                "name": t.name,
                "value": t.value,
                "direction": t.direction,
                "color": t.hex_color,
                "active": bool(active.get(t.id)),
            }
            for t in s.thresholds
        ],
    }


def _stage_attrs(model: LevelWatchModel) -> dict[str, Any]:
    stage = model.snapshot.stage
    return {
        "color": _color(model),
        "value": stage.value if stage else None,
        "direction": stage.direction if stage else None,
    }


def _next_attrs(model: LevelWatchModel) -> dict[str, Any]:
    nxt = model.snapshot.next_threshold
    return {
        "value": nxt.value if nxt else None,
        "direction": nxt.direction if nxt else None,
        "color": nxt.hex_color if nxt else None,
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
        key="stage",
        translation_key="stage",
        icon="mdi:alert-octagon-outline",
        value_fn=lambda s: s.stage.name if s.stage else STAGE_NORMAL,
        attrs_fn=_stage_attrs,
    ),
    LevelSensorDescription(
        key="next_threshold",
        translation_key="next_threshold",
        icon="mdi:debug-step-over",
        value_fn=lambda s: s.next_threshold.name if s.next_threshold else None,
        attrs_fn=_next_attrs,
    ),
    LevelSensorDescription(
        key="time_to_next",
        translation_key="time_to_next",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        value_fn=lambda s: s.hours_to_next,
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

THRESHOLD_KEYS = {"stage", "next_threshold", "time_to_next"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LevelWatchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    model = entry.runtime_data
    s = model.settings

    def wanted(d: LevelSensorDescription) -> bool:
        if d.key == "percent":
            return s.ref_max is not None
        if d.key in THRESHOLD_KEYS:
            return bool(s.thresholds)
        return True

    async_add_entities(LevelSensor(entry, model, d) for d in SENSORS if wanted(d))


class LevelSensor(LevelWatchEntity, SensorEntity):
    """One derived value of a monitored level."""

    entity_description: LevelSensorDescription

    def __init__(
        self,
        entry: LevelWatchConfigEntry,
        model: LevelWatchModel,
        description: LevelSensorDescription,
    ) -> None:
        super().__init__(entry, model, description.key)
        self.entity_description = description

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
        return self.entity_description.icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self._model)
