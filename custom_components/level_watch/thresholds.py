"""Thresholds: configuration, crossing logic with hysteresis and messages.

Nothing in here imports Home Assistant, so the logic can be tested on its own.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

ABOVE = "above"
BELOW = "below"
DIRECTIONS = [ABOVE, BELOW]

DEFAULT_HYSTERESIS = 2.0  # cm
DEFAULT_ABOVE_COLOR = (245, 124, 0)
DEFAULT_BELOW_COLOR = (25, 118, 210)
NORMAL_COLOR = "#26a69a"


@dataclass(frozen=True, slots=True)
class Threshold:
    id: str
    name: str
    value: float
    direction: str
    hysteresis: float = DEFAULT_HYSTERESIS
    color: tuple[int, int, int] = DEFAULT_ABOVE_COLOR
    notify: bool = False
    targets: tuple[str, ...] = ()
    critical: bool = False
    message: str = ""
    clear_message: bool = True
    repeat: float = 0.0  # minutes, 0 = once

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Threshold:
        direction = data.get("direction", ABOVE)
        default_color = DEFAULT_ABOVE_COLOR if direction == ABOVE else DEFAULT_BELOW_COLOR
        color = data.get("color") or default_color
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or data["id"]),
            value=float(data["value"]),
            direction=direction,
            hysteresis=float(data.get("hysteresis") or 0.0),
            color=(int(color[0]), int(color[1]), int(color[2])),
            notify=bool(data.get("notify")),
            targets=tuple(data.get("targets") or ()),
            critical=bool(data.get("critical")),
            message=str(data.get("message") or ""),
            clear_message=bool(data.get("clear_message", True)),
            repeat=float(data.get("repeat") or 0.0),
        )

    @property
    def hex_color(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self.color)

    def is_active(self, level: float, was_active: bool) -> bool:
        """Whether the threshold holds at this level.

        Once active it only clears after moving back by the hysteresis, so a
        level wobbling around the threshold does not toggle it constantly.
        """
        if self.direction == ABOVE:
            if was_active:
                return level > self.value - self.hysteresis
            return level >= self.value
        if was_active:
            return level < self.value + self.hysteresis
        return level <= self.value


def load_thresholds(raw: Iterable[Mapping[str, Any]] | None) -> list[Threshold]:
    return sorted(
        (Threshold.from_dict(item) for item in raw or ()), key=lambda t: t.value
    )


def stage(thresholds: Iterable[Threshold], active: Mapping[str, bool]) -> Threshold | None:
    """The most severe active threshold.

    For thresholds crossed upwards that is the highest one, for thresholds
    crossed downwards the lowest. Upward thresholds win if both kinds are
    active (a flood warning matters more than a low-water note).
    """
    hits = [t for t in thresholds if active.get(t.id)]
    above = [t for t in hits if t.direction == ABOVE]
    if above:
        return max(above, key=lambda t: t.value)
    below = [t for t in hits if t.direction == BELOW]
    return min(below, key=lambda t: t.value) if below else None


def next_threshold(
    thresholds: Iterable[Threshold],
    active: Mapping[str, bool],
    level: float,
    rate: float | None,
) -> Threshold | None:
    """The next inactive threshold the level is moving towards."""
    if not rate:
        return None
    if rate > 0:
        ahead = [
            t for t in thresholds
            if t.direction == ABOVE and not active.get(t.id) and t.value > level
        ]
        return min(ahead, key=lambda t: t.value) if ahead else None
    ahead = [
        t for t in thresholds
        if t.direction == BELOW and not active.get(t.id) and t.value < level
    ]
    return max(ahead, key=lambda t: t.value) if ahead else None


# -- presets ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PresetItem:
    key: str
    names: Mapping[str, str]  # language -> name
    direction: str
    color: tuple[int, int, int]
    critical_allowed: bool = False  # the "critical" switch applies to this one


PRESETS: dict[str, tuple[PresetItem, ...]] = {
    "river": (
        PresetItem("low", {"de": "Niedrigwasser", "en": "Low water"}, BELOW, (25, 118, 210)),
        PresetItem("stage1", {"de": "Meldestufe 1", "en": "Warning level 1"}, ABOVE, (251, 192, 45)),
        PresetItem("stage2", {"de": "Meldestufe 2", "en": "Warning level 2"}, ABOVE, (245, 124, 0)),
        PresetItem(
            "stage3", {"de": "Meldestufe 3", "en": "Warning level 3"}, ABOVE, (229, 57, 53), True
        ),
        PresetItem(
            "stage4", {"de": "Meldestufe 4", "en": "Warning level 4"}, ABOVE, (142, 36, 170), True
        ),
    ),
    "tank": (
        PresetItem(
            "empty", {"de": "Fast leer", "en": "Almost empty"}, BELOW, (229, 57, 53), True
        ),
        PresetItem("reserve", {"de": "Reserve", "en": "Reserve"}, BELOW, (245, 124, 0)),
        PresetItem("full", {"de": "Voll", "en": "Full"}, ABOVE, (25, 118, 210)),
    ),
}
PRESET_HYSTERESIS = {"river": 5.0, "tank": 2.0}


def preset_thresholds(
    preset: str,
    values: Mapping[str, float | None],
    *,
    language: str | None,
    notify: bool,
    targets: Iterable[str],
    critical: bool,
    new_id: Callable[[], str],
) -> list[dict[str, Any]]:
    """Threshold dicts for the preset items that got a value."""
    lang = "de" if (language or "").lower().startswith("de") else "en"
    result = []
    for item in PRESETS[preset]:
        value = values.get(item.key)
        if value is None:
            continue
        result.append(
            {
                "id": new_id(),
                "name": item.names[lang],
                "value": float(value),
                "direction": item.direction,
                "hysteresis": PRESET_HYSTERESIS[preset],
                "color": list(item.color),
                "notify": notify,
                "targets": list(targets) if notify else [],
                "critical": critical and item.critical_allowed,
                "message": "",
                "clear_message": True,
                "repeat": 0,
            }
        )
    return result


# -- messages -----------------------------------------------------------------

TEXTS = {
    "de": {
        "test": "Test",
        "title": "Level Watch meldet: {name}",
        "alert": "{name}: {threshold} erreicht. Pegel {level} {unit}, {trend} ({rate} {unit}/h).",
        "clear": "{name}: {threshold} aufgehoben. Pegel {level} {unit}, {trend}.",
        "rising": "steigend",
        "falling": "fallend",
        "stable": "stabil",
        "unknown": "Tendenz unbekannt",
    },
    "en": {
        "test": "Test",
        "title": "Level Watch reports: {name}",
        "alert": "{name}: {threshold} reached. Level {level} {unit}, {trend} ({rate} {unit}/h).",
        "clear": "{name}: {threshold} cleared. Level {level} {unit}, {trend}.",
        "rising": "rising",
        "falling": "falling",
        "stable": "stable",
        "unknown": "trend unknown",
    },
}


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def texts(language: str | None) -> dict[str, str]:
    return TEXTS["de" if (language or "").lower().startswith("de") else "en"]


def format_message(
    template: str,
    *,
    language: str | None,
    name: str,
    threshold: Threshold,
    level: float,
    trend: str | None,
    rate: float | None,
    cleared: bool = False,
    unit: str = "cm",
) -> str:
    """Fill the user's template (or the default one) with current values.

    Unknown placeholders stay as written instead of failing.
    """
    t = texts(language)
    comma = t is TEXTS["de"]

    def num(value: float, signed: bool = False) -> str:
        text = _fmt(value, signed)
        return text.replace(".", ",") if comma else text

    if not template or cleared:
        template = t["clear" if cleared else "alert"]
    values = _SafeDict(
        name=name,
        threshold=threshold.name,
        value=num(threshold.value),
        level=num(level),
        trend=t.get(trend or "unknown", t["unknown"]),
        rate="?" if rate is None else num(rate, signed=True),
        unit=unit,
    )
    try:
        return template.format_map(values)
    except (ValueError, IndexError):
        return template  # stray braces: send the text as written


def _fmt(value: float, signed: bool = False) -> str:
    text = f"{value:+.1f}" if signed else f"{value:.1f}"
    return text.removesuffix(".0")
