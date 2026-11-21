"""Tank geometry and consumption forecast.

Nothing in here imports Home Assistant. Levels in cm, volumes in litres.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from .calc import LevelHistory, slope_per_second

NONE = "none"
VERTICAL = "vertical_cylinder"
HORIZONTAL = "horizontal_cylinder"
BOX = "box"
SHAPES = [NONE, VERTICAL, HORIZONTAL, BOX]

# Below this consumption the range is effectively endless, so none is shown.
MIN_CONSUMPTION = 0.01  # L/d


@dataclass(frozen=True, slots=True)
class TankShape:
    shape: str
    diameter: float | None = None  # cm, cylinders
    length: float | None = None  # cm, horizontal cylinder and box
    width: float | None = None  # cm, box

    @property
    def defined(self) -> bool:
        return not self.missing()

    def missing(self) -> list[str]:
        """Dimensions the shape needs but does not have."""
        need = {
            NONE: [],
            VERTICAL: ["diameter"],
            HORIZONTAL: ["diameter", "length"],
            BOX: ["length", "width"],
        }.get(self.shape, [])
        if self.shape == NONE:
            return ["shape"]
        return [k for k in need if not getattr(self, k)]

    @property
    def max_height(self) -> float | None:
        """Height at which the tank is geometrically full, if the shape says so."""
        return self.diameter if self.shape == HORIZONTAL else None

    def volume(self, level: float) -> float:
        """Litres at the level above the tank bottom (clamped to the shape)."""
        h = max(0.0, level)
        if self.shape == VERTICAL:
            return math.pi * (self.diameter / 2) ** 2 * h / 1000
        if self.shape == BOX:
            return self.length * self.width * h / 1000
        if self.shape == HORIZONTAL:
            r = self.diameter / 2
            h = min(h, self.diameter)
            # Area of the circular segment filled up to height h.
            area = r * r * math.acos((r - h) / r) - (r - h) * math.sqrt(2 * r * h - h * h)
            return area * self.length / 1000
        raise ValueError(f"no volume for shape {self.shape!r}")


def capacity(shape: TankShape, ref_max: float | None) -> float | None:
    top = ref_max if ref_max is not None else shape.max_height
    return None if top is None else shape.volume(top)


def volume_percent(
    shape: TankShape, level: float, ref_min: float, ref_max: float | None
) -> float | None:
    """Fill level by volume; differs from height for a horizontal cylinder."""
    top = ref_max if ref_max is not None else shape.max_height
    if top is None or top <= ref_min:
        return None
    low = shape.volume(ref_min)
    full = shape.volume(top) - low
    if full <= 0:
        return None
    return max(0.0, min(100.0, (shape.volume(level) - low) / full * 100))


def is_refill(long: LevelHistory, now: float, level: float, jump: float) -> bool:
    """True if the level rose by at least `jump` cm within the last two hours."""
    if jump <= 0:
        return False
    recent = long.since(now - 7200)
    return bool(recent) and level - min(s.value for s in recent) >= jump


def consumption_per_day(
    shape: TankShape, long: LevelHistory, now: float, window: float, min_span: float
) -> float | None:
    """Average litres per day taken out, from the samples since the last refill.

    Negative values (the tank is filling, e.g. rain in a cistern) count as zero.
    """
    samples = long.since(now - window)
    if len(samples) < 3 or samples[-1].ts - samples[0].ts < min_span:
        return None
    slope = slope_per_second(samples, shape.volume)
    if slope is None:
        return None
    return max(0.0, -slope * 86400)


def days_left(
    shape: TankShape, level: float, ref_min: float, consumption: float | None
) -> float | None:
    """Days until the level reaches the bottom reference at this consumption."""
    if consumption is None or consumption < MIN_CONSUMPTION:
        return None
    usable = shape.volume(level) - shape.volume(ref_min)
    return max(0.0, usable) / consumption


def hours_to_full(level: float, ref_max: float | None, rate: float | None) -> float | None:
    """Hours until the top reference at the current rise in cm/h."""
    if ref_max is None or not rate or rate <= 0 or level >= ref_max:
        return None
    return (ref_max - level) / rate
